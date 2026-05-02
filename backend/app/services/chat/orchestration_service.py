"""
Chat orchestration service for REEVU.

Owns the full sync and streaming chat request lifecycle.
Extracted from backend/app/api/v2/chat.py so that chat.py becomes a thin router.
"""
import contextlib
import logging
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from time import perf_counter
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import asyncio

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import User
from app.modules.ai.services.capability_registry import CapabilityRegistry
from app.modules.ai.services.engine import ConversationMessage, LLMProvider
from app.modules.ai.services.function_calling_service import (
    ClarificationResponse,
    FunctionCallingService,
)
from app.modules.ai.services.quota import AIQuotaService
from app.modules.ai.services.reevu import PolicyGuard, ReevuMetrics, ReevuStage
from app.modules.ai.services.reevu_service import ReevuService
from app.modules.ai.services.response_enrichment_service import ResponseEnrichmentService
from app.modules.ai.services.tools import FunctionExecutor
from app.modules.breeding.services.breeding_value_service import breeding_value_service
from app.modules.breeding.services.cross_search_service import cross_search_service
from app.modules.breeding.services.speed_breeding_service import speed_breeding_service
from app.modules.breeding.services.trial_search_service import trial_search_service
from app.modules.environment.services.weather_service import weather_service
from app.modules.germplasm.services.search_service import germplasm_search_service
from app.modules.spatial.services.location_search_service import location_search_service
from app.schemas.chat import ChatResponse, ContextDocument
from app.schemas.reevu_chat_context import ReevuScopedChatContext

from .context_service import ContextService
from .message_service import MessageService
from .session_service import SessionService
from .streaming_service import StreamingService

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Owns the full sync and streaming chat request lifecycle."""

    def __init__(
        self,
        db: AsyncSession,
        current_user: User,
        reevu_service: ReevuService,
    ) -> None:
        self.db = db
        self.current_user = current_user
        self.reevu_service = reevu_service
        self.user_id = int(current_user.id)
        self.organization_id = int(current_user.organization_id)
        self.user_ref = SimpleNamespace(id=self.user_id, organization_id=self.organization_id)

    # ------------------------------------------------------------------ #
    # Shared setup helpers                                                 #
    # ------------------------------------------------------------------ #

    async def _setup_session(self) -> tuple[Any, Any, CapabilityRegistry]:
        """Return (llm_service, agent_setting, capability_registry)."""
        llm_service = await SessionService.get_request_llm_service(self.db, self.current_user)
        agent_setting = await SessionService.get_request_agent_setting(self.db, self.current_user)
        if agent_setting is None:
            capability_registry = CapabilityRegistry()
        else:
            capability_registry = CapabilityRegistry.from_agent_setting(agent_setting)
        return llm_service, agent_setting, capability_registry

    async def _enforce_quota(self, user_api_key: str | None) -> None:
        """Increment daily quota unless the user supplies their own key."""
        await SessionService.enforce_quota(self.db, self.organization_id, user_api_key)

    async def _init_user_context(self) -> None:
        await self.reevu_service.get_or_create_user_context(self.user_ref)
        await self.reevu_service.update_interaction_stats(self.user_id)

    def _build_function_executor(self, capability_registry: CapabilityRegistry) -> FunctionExecutor:
        return FunctionExecutor(
            self.db,
            capability_registry=capability_registry,
            cross_search_service=cross_search_service,
            trial_search_service=trial_search_service,
            germplasm_search_service=germplasm_search_service,
            location_search_service=location_search_service,
            weather_service=weather_service,
            breeding_value_service=breeding_value_service,
            protocol_search_service=speed_breeding_service,
        )

    # ------------------------------------------------------------------ #
    # Sync chat handler                                                    #
    # ------------------------------------------------------------------ #

    async def handle_chat(self, request: Any) -> dict[str, Any]:
        """Execute a synchronous chat request and return a ChatResponse-compatible dict."""
        llm_service, agent_setting, capability_registry = await self._setup_session()
        await self._enforce_quota(request.user_api_key)
        await self._init_user_context()

        request_id = str(uuid4())
        start_time = perf_counter()
        context_docs = None
        context_response = None
        context_doc_ids: list[str] = []
        scoped_task_context = ContextService.format_task_context_for_llm(request.task_context)
        plan_summary: dict[str, Any] | None = None

        function_calling_service = FunctionCallingService(
            api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY"),
            function_schemas=capability_registry.get_allowed_functions(),
        )

        # --- Function call path ---
        try:
            function_call = await function_calling_service.detect_function_call(
                user_message=request.message,
                conversation_history=[msg.model_dump() for msg in (request.conversation_history or [])],
            )
            if isinstance(function_call, ClarificationResponse):
                clarification_payload = function_call.to_dict()
                ReevuMetrics.get().record_request(
                    domain="clarification",
                    function_name="clarification_required",
                    status="clarification",
                    latency_seconds=perf_counter() - start_time,
                    stage="total",
                    provider="deterministic_function",
                )
                return ChatResponse(
                    request_id=request_id,
                    message=function_call.message,
                    provider="deterministic_function",
                    model="function:clarification",
                    model_confirmed=False,
                    context=None,
                    conversation_id=request.conversation_id,
                    suggestions=[
                        option.description for option in function_call.options
                    ],
                    cached=False,
                    function_call=None,
                    function_result={
                        "result_type": "clarification_required",
                        "clarification": clarification_payload,
                    },
                    policy_validation={
                        "valid": True,
                        "error_count": 0,
                        "errors": [],
                        "evidence_count": 0,
                        "calculation_count": 0,
                    },
                    plan_execution_summary={
                        "clarification_required": True,
                        "domains_involved": [],
                        "is_compound": False,
                    },
                )
            plan_summary = MessageService.build_plan_summary(
                request.message,
                function_call_name=function_call.name if function_call else None,
            )

            if function_call:
                logger.info("[REEVU] Function call detected: %s", function_call.name)
                function_executor = self._build_function_executor(capability_registry)
                try:
                    execution_parameters = {**function_call.parameters, "organization_id": self.organization_id}
                    function_result = await function_executor.execute(function_call.name, execution_parameters)
                    function_call_data = function_call.to_dict()
                    function_result = await ResponseEnrichmentService.enrich(
                        function_call.name, function_result, self.db, self.organization_id
                    )

                    response_message = MessageService.extract_function_response_message(function_result)
                    response_provider = "deterministic_function"
                    response_model = f"function:{function_call.name}"
                    response_model_confirmed = False
                    response_latency_ms: float | None = None
                    llm_response = None

                    if response_message is None:
                        llm_response = await llm_service.chat(
                            user_message=MessageService.build_function_explanation_prompt(
                                request_message=request.message,
                                function_name=function_call.name,
                                function_parameters=function_call.parameters,
                                function_result=function_result,
                            ),
                            conversation_history=None,
                            context=scoped_task_context or None,
                            organization_id=self.organization_id,
                            user_id=self.user_id,
                            system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
                            prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
                        )
                        response_message = llm_response.content
                        response_provider = llm_response.provider.value
                        response_model = llm_response.model
                        response_model_confirmed = llm_response.model_confirmed
                        response_latency_ms = llm_response.latency_ms

                    if llm_response is not None and not request.user_api_key and not llm_response.cached:
                        try:
                            await AIQuotaService.record_generation_usage(
                                self.db, self.organization_id,
                                tokens_input=getattr(llm_response, "input_tokens", None),
                                tokens_output=getattr(llm_response, "output_tokens", None),
                            )
                        except Exception as _quota_exc:
                            logger.error(
                                "[REEVU] Quota recording failed (billing data lost) org=%s: %s",
                                self.organization_id, _quota_exc,
                            )

                    validation, evidence_pack = MessageService.validate_response_content(
                        content=response_message,
                        context_docs=context_docs,
                        function_call_name=function_call.name,
                        function_result=function_result,
                    )
                    policy_validation_payload: dict[str, Any] = {
                        "valid": validation.valid,
                        "error_count": len(validation.errors),
                        "errors": list(validation.errors),
                        "evidence_count": len(evidence_pack.evidence_refs),
                        "calculation_count": len(evidence_pack.calculation_ids),
                    }
                    if not validation.valid:
                        policy_validation_payload["safe_failure"] = MessageService.build_safe_failure_payload(
                            error_category="insufficient_evidence",
                            searched=["function_result", "retrieved_context", "response_validation"],
                            missing=["grounded evidence for one or more claims"],
                            next_steps=[
                                "Retry with narrower filters (crop, trial, location, season).",
                                "Request source IDs and verify records before action.",
                            ],
                        )
                        response_message = (
                            "I could not fully verify this answer against current evidence. "
                            "Please rerun with more specific filters or review source records before taking action."
                        )

                    retrieval_audit_payload = MessageService.build_response_retrieval_audit(
                        request_message=request.message,
                        function_result=function_result,
                    )
                    executed_plan_summary = MessageService.extract_plan_execution_summary(function_result, plan_summary)
                    total_latency = perf_counter() - start_time
                    routing_state = SessionService.get_llm_routing_state(llm_service)
                    ReevuMetrics.get().record_request(
                        domain=MessageService.get_primary_domain(executed_plan_summary),
                        function_name=function_call.name,
                        status="safe_failure" if not validation.valid else "ok",
                        latency_seconds=total_latency,
                        stage="total",
                        policy_flags=list(validation.errors) if validation else [],
                        provider=response_provider,
                        safe_failure_reason="insufficient_evidence" if not validation.valid else None,
                        routing_decisions=SessionService.derive_routing_decisions(
                            requested_provider=request.preferred_provider,
                            actual_provider=response_provider,
                            routing_state=routing_state,
                        ),
                        retrieval_audit=retrieval_audit_payload,
                        plan_execution_summary=executed_plan_summary,
                    )

                    return ChatResponse(
                        request_id=request_id,
                        message=response_message,
                        provider=response_provider,
                        model=response_model,
                        model_confirmed=response_model_confirmed,
                        context=None,
                        conversation_id=request.conversation_id,
                        suggestions=["Show me more details", "Export this data", "What else can you do?"],
                        cached=False,
                        latency_ms=response_latency_ms,
                        function_call=function_call_data,
                        function_result=function_result,
                        policy_validation=policy_validation_payload,
                        evidence_envelope=MessageService.build_reevu_envelope(
                            content=response_message,
                            evidence_pack=evidence_pack,
                            validation=validation,
                            context_docs=context_docs,
                            function_call_name=function_call.name,
                        ),
                        retrieval_audit=retrieval_audit_payload,
                        plan_execution_summary=executed_plan_summary,
                        comparison_result=MessageService.maybe_format_comparison(
                            function_result,
                            function_call_name=function_call.name,
                        ),
                    )

                except Exception as exc:
                    logger.error("[REEVU] Function execution error: %s", exc)
                    # Fall through to regular chat

        except Exception as exc:
            logger.warning("[REEVU] Function detection error: %s, proceeding with regular chat", exc)
            with contextlib.suppress(Exception):
                plan_summary = MessageService.build_plan_summary(request.message)

        # --- Regular conversational path ---
        if request.include_context:
            try:
                breeding_svc = await SessionService.get_breeding_service(self.db)
                context_docs = await breeding_svc.search_breeding_knowledge(
                    query=request.message,
                    limit=request.context_limit,
                )
                if context_docs:
                    context_doc_ids = [doc.doc_id for doc in context_docs]
                    context_response = [
                        ContextDocument(
                            doc_id=doc.doc_id,
                            doc_type=doc.doc_type,
                            title=doc.title,
                            content=doc.content[:500],
                            similarity=doc.similarity,
                            source_id=doc.source_id,
                        )
                        for doc in context_docs
                    ]
            except Exception as exc:
                logger.warning("[REEVU] Context retrieval error: %s", exc)

        context_text = ContextService.merge_prompt_context(
            scoped_task_context,
            ContextService.format_context_for_llm(context_docs) if context_docs else "",
        )

        history = None
        if request.conversation_history:
            history = [
                ConversationMessage(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp or datetime.now(UTC),
                )
                for msg in request.conversation_history
            ]

        preferred = None
        if request.preferred_provider:
            with contextlib.suppress(ValueError):
                preferred = LLMProvider(request.preferred_provider.lower())

        llm_response = await llm_service.chat(
            user_message=request.message,
            conversation_history=history,
            context=context_text,
            preferred_provider=preferred,
            organization_id=self.organization_id,
            user_id=self.user_id,
            user_api_key=request.user_api_key,
            user_model=request.user_model,
            system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
            prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
        )

        if not request.user_api_key and not llm_response.cached:
            try:
                await AIQuotaService.record_generation_usage(
                    self.db, self.organization_id,
                    tokens_input=getattr(llm_response, "input_tokens", None),
                    tokens_output=getattr(llm_response, "output_tokens", None),
                )
            except Exception as _quota_exc:
                logger.error(
                    "[REEVU] Quota recording failed (billing data lost) org=%s: %s",
                    self.organization_id, _quota_exc,
                )

        validation, evidence_pack = MessageService.validate_response_content(
            content=llm_response.content,
            context_docs=context_docs,
            function_call_name=None,
            function_result=None,
        )
        policy_validation_payload = {
            "valid": validation.valid,
            "error_count": len(validation.errors),
            "errors": list(validation.errors),
            "evidence_count": len(evidence_pack.evidence_refs),
            "calculation_count": len(evidence_pack.calculation_ids),
        }
        if not validation.valid:
            policy_validation_payload["safe_failure"] = MessageService.build_safe_failure_payload(
                error_category="insufficient_evidence",
                searched=["retrieved_context", "response_validation"],
                missing=["grounded evidence for one or more claims"],
                next_steps=[
                    "Narrow the question by crop, trial, location, or date range.",
                    "Ask for cited record IDs and verify before decisions.",
                ],
            )
            llm_response.content = (
                "I cannot verify all claims in a grounded way from the currently available evidence. "
                "Try a narrower query or provide additional context to improve confidence."
            )

        if llm_response.content:
            with contextlib.suppress(Exception):
                await self.reevu_service.save_episodic_memory(
                    user=self.user_ref,
                    content=f"User: {request.message}\nREEVU: {llm_response.content[:200]}...",
                    source_type="chat",
                    importance=0.3,
                )

        total_latency = perf_counter() - start_time
        routing_state = SessionService.get_llm_routing_state(llm_service)
        retrieval_audit_payload = MessageService.build_response_retrieval_audit(
            request_message=request.message,
            context_retrieval_attempted=request.include_context,
            context_doc_ids=context_doc_ids,
        )
        ReevuMetrics.get().record_request(
            domain=MessageService.get_primary_domain(plan_summary),
            function_name="",
            status="safe_failure" if not validation.valid else "ok",
            latency_seconds=total_latency,
            stage="total",
            policy_flags=list(validation.errors) if validation else [],
            provider=llm_response.provider.value,
            safe_failure_reason="insufficient_evidence" if not validation.valid else None,
            routing_decisions=SessionService.derive_routing_decisions(
                requested_provider=request.preferred_provider,
                actual_provider=llm_response.provider.value,
                routing_state=routing_state,
            ),
            retrieval_audit=retrieval_audit_payload,
            plan_execution_summary=plan_summary,
        )

        return ChatResponse(
            request_id=request_id,
            message=llm_response.content,
            provider=llm_response.provider.value,
            model=llm_response.model,
            model_confirmed=llm_response.model_confirmed,
            context=context_response,
            conversation_id=request.conversation_id,
            suggestions=MessageService.generate_suggestions(request.message, llm_response.content),
            cached=llm_response.cached,
            latency_ms=llm_response.latency_ms,
            policy_validation=policy_validation_payload,
            evidence_envelope=MessageService.build_reevu_envelope(
                content=llm_response.content,
                evidence_pack=evidence_pack,
                validation=validation,
                context_docs=context_docs,
                function_call_name=None,
            ),
            retrieval_audit=retrieval_audit_payload,
            plan_execution_summary=plan_summary,
        )

    # ------------------------------------------------------------------ #
    # Streaming chat handler                                               #
    # ------------------------------------------------------------------ #

    async def handle_stream(self, request: Any) -> AsyncGenerator[str, None]:
        """Generate SSE events for a streaming chat request."""
        llm_service, agent_setting, capability_registry = await self._setup_session()
        await self._enforce_quota(request.user_api_key)
        await self._init_user_context()

        policy_guard = PolicyGuard()
        context_docs = None
        context_text = None
        context_doc_ids: list[str] = []
        scoped_task_context = ContextService.format_task_context_for_llm(request.task_context)
        request_id = str(uuid4())
        streaming_svc = StreamingService(request_id)
        start_time = perf_counter()

        if request.include_context:
            try:
                access_decision = policy_guard.evaluate_access(
                    domain_scope="breeding",
                    entity="breeding_knowledge",
                    operation="read",
                )
                if not access_decision.allowed:
                    raise HTTPException(status_code=403, detail=access_decision.reason)
                breeding_svc = await SessionService.get_breeding_service(self.db)
                context_docs = await breeding_svc.search_breeding_knowledge(
                    query=request.message,
                    limit=request.context_limit,
                )
                if context_docs:
                    context_text = ContextService.format_context_for_llm(context_docs)
                    context_doc_ids = [doc.doc_id for doc in context_docs]
            except Exception as exc:
                logger.warning("[REEVU] Context retrieval error for streaming: %s", exc)

        context_text = ContextService.merge_prompt_context(scoped_task_context, context_text or "")

        history = None
        if request.conversation_history:
            history = [
                ConversationMessage(
                    role=msg.role,
                    content=msg.content,
                    timestamp=msg.timestamp or datetime.now(UTC),
                )
                for msg in request.conversation_history
            ]

        preferred = None
        if request.preferred_provider:
            with contextlib.suppress(ValueError):
                preferred = LLMProvider(request.preferred_provider.lower())

        async def _generate() -> AsyncGenerator[str, None]:
            try:
                yield streaming_svc.stage_event(ReevuStage.INTENT_SCOPE, "started")

                function_calling_service = FunctionCallingService(
                    api_key=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("FUNCTIONGEMMA_API_KEY"),
                    function_schemas=capability_registry.get_allowed_functions(),
                )

                function_call = None
                function_result = None
                clarification_response = None
                prompt_override = None
                accumulated_response = ""
                plan_summary: dict[str, Any] | None = None

                try:
                    yield streaming_svc.stage_event(ReevuStage.PLAN_GENERATION, "started")
                    function_call = await function_calling_service.detect_function_call(
                        user_message=request.message,
                        conversation_history=[msg.model_dump() for msg in (request.conversation_history or [])],
                    )
                    if isinstance(function_call, ClarificationResponse):
                        clarification_response = function_call
                        function_call = None
                    plan_summary = MessageService.build_plan_summary(
                        request.message,
                        function_call_name=function_call.name if function_call else None,
                    )
                    yield streaming_svc.stage_event(
                        ReevuStage.PLAN_GENERATION,
                        "completed",
                        function_call_detected=bool(function_call),
                        clarification_required=bool(clarification_response),
                        plan_is_compound=bool(plan_summary.get("is_compound")),
                        domains_involved=plan_summary.get("domains_involved", []),
                    )
                except Exception as exc:
                    logger.warning("[REEVU] Function detection failed: %s", exc)
                    with contextlib.suppress(Exception):
                        plan_summary = MessageService.build_plan_summary(request.message)
                    yield streaming_svc.stage_event(ReevuStage.PLAN_GENERATION, "failed", error=str(exc))

                actual_provider = "unknown"
                actual_model = "unknown"
                if request.user_api_key and request.preferred_provider:
                    actual_provider = request.preferred_provider
                    actual_model = request.user_model or "default"
                else:
                    status = await llm_service.get_status()
                    actual_provider = status.get("active_provider", "unknown")
                    actual_model = status.get("active_model", "unknown")

                yield streaming_svc.start_event(actual_provider, actual_model)

                if clarification_response is not None:
                    yield streaming_svc.chunk_event(clarification_response.message)
                    yield streaming_svc.summary_event(
                        {
                            "function_result": {
                                "result_type": "clarification_required",
                                "clarification": clarification_response.to_dict(),
                            },
                            "plan_execution_summary": {
                                "clarification_required": True,
                                "domains_involved": [],
                                "is_compound": False,
                            },
                        }
                    )
                    yield streaming_svc.done_event()
                    ReevuMetrics.get().record_request(
                        domain="clarification",
                        function_name="clarification_required",
                        status="clarification",
                        latency_seconds=perf_counter() - start_time,
                        stage="total",
                        provider=actual_provider,
                    )
                    return

                has_byok = request.user_api_key and request.preferred_provider
                if not has_byok and not function_call:
                    status = await llm_service.get_status()
                    if StreamingService.is_template_only_mode(status):
                        for evt in streaming_svc.template_mode_events():
                            yield evt
                        return

                function_response_message: str | None = None
                if function_call:
                    logger.info("[REEVU] Executing function in stream: %s", function_call.name)
                    yield streaming_svc.stage_event(ReevuStage.DATA_EXECUTION, "started", function_name=function_call.name)
                    function_executor = self._build_function_executor(capability_registry)
                    try:
                        execution_parameters = {**function_call.parameters, "organization_id": self.organization_id}
                        function_result = await function_executor.execute(function_call.name, execution_parameters)
                        yield streaming_svc.stage_event(ReevuStage.DATA_EXECUTION, "completed", function_name=function_call.name)

                        if function_result.get("result_type") == "proposal_created":
                            yield streaming_svc.proposal_event(function_result.get("data", {}))

                        function_result = await ResponseEnrichmentService.enrich(
                            function_call.name, function_result, self.db, self.organization_id
                        )
                        function_response_message = MessageService.extract_function_response_message(function_result)
                        if function_response_message is None:
                            prompt_override = MessageService.build_function_explanation_prompt(
                                request_message=request.message,
                                function_name=function_call.name,
                                function_parameters=function_call.parameters,
                                function_result=function_result,
                            )
                    except Exception as exc:
                        logger.error("[REEVU] Function execution error: %s", exc)
                        yield streaming_svc.stage_event(ReevuStage.DATA_EXECUTION, "failed", error=str(exc))
                        yield streaming_svc.chunk_event(f"\n\n[Error executing action: {exc}]")

                yield streaming_svc.stage_event(ReevuStage.ANSWER_SYNTHESIS, "started")
                chunk_count = 0
                if function_response_message is not None:
                    yield streaming_svc.chunk_event(function_response_message)
                    accumulated_response = function_response_message
                else:
                    message_to_send = prompt_override if prompt_override else request.message
                    async for chunk in llm_service.stream_chat(
                        user_message=message_to_send,
                        conversation_history=history if not prompt_override else None,
                        context=context_text,
                        preferred_provider=preferred,
                        user_api_key=request.user_api_key,
                        user_model=request.user_model,
                        system_prompt_override=getattr(agent_setting, "system_prompt_override", None),
                        prompt_mode_capabilities=getattr(agent_setting, "prompt_mode_capabilities", None),
                    ):
                        yield streaming_svc.chunk_event(chunk)
                        accumulated_response += chunk
                        chunk_count += 1
                        if chunk_count % 50 == 0:
                            yield StreamingService.keepalive()

                if accumulated_response:
                    with contextlib.suppress(Exception):
                        await self.reevu_service.save_episodic_memory(
                            user=self.user_ref,
                            content=f"User: {request.message}\nREEVU: {accumulated_response[:200]}...",
                            source_type="chat",
                            importance=0.3,
                        )

                yield streaming_svc.stage_event(ReevuStage.ANSWER_SYNTHESIS, "completed")

                yield streaming_svc.stage_event(ReevuStage.POLICY_VALIDATION, "started")
                validation, evidence_pack = MessageService.validate_response_content(
                    content=accumulated_response,
                    context_docs=context_docs if request.include_context else None,
                    function_call_name=function_call.name if function_call else None,
                    function_result=function_result,
                )
                policy_stage_payload: dict[str, Any] = {
                    "valid": validation.valid,
                    "error_count": len(validation.errors),
                    "evidence_count": len(evidence_pack.evidence_refs),
                    "calculation_count": len(evidence_pack.calculation_ids),
                }
                if not validation.valid:
                    policy_stage_payload["safe_failure"] = MessageService.build_safe_failure_payload(
                        error_category="insufficient_evidence",
                        searched=["stream_response", "retrieved_context", "response_validation"],
                        missing=["grounded evidence for one or more claims"],
                        next_steps=[
                            "Narrow the query by crop, trial, location, or season.",
                            "Request cited record IDs and verify before decisions.",
                        ],
                    )
                yield streaming_svc.stage_event(ReevuStage.POLICY_VALIDATION, "completed", **policy_stage_payload)
                yield streaming_svc.stage_event(ReevuStage.RESPONSE_EMISSION, "completed")

                envelope_dict = MessageService.build_reevu_envelope(
                    content=accumulated_response,
                    evidence_pack=evidence_pack,
                    validation=validation,
                    context_docs=context_docs if request.include_context else None,
                    function_call_name=function_call.name if function_call else None,
                )
                summary_payload: dict[str, Any] = {"evidence_envelope": envelope_dict}
                retrieval_audit = MessageService.build_response_retrieval_audit(
                    request_message=request.message,
                    function_result=function_result,
                    context_retrieval_attempted=request.include_context,
                    context_doc_ids=context_doc_ids,
                )
                if retrieval_audit:
                    summary_payload["retrieval_audit"] = retrieval_audit
                executed_plan_summary = MessageService.extract_plan_execution_summary(function_result, plan_summary)
                if executed_plan_summary:
                    summary_payload["plan_execution_summary"] = executed_plan_summary
                summary_safe_failure = MessageService.extract_summary_safe_failure(function_result, validation)
                if summary_safe_failure:
                    summary_payload["safe_failure"] = summary_safe_failure
                comparison = MessageService.maybe_format_comparison(
                    function_result,
                    function_call_name=function_call.name if function_call else None,
                )
                if comparison:
                    summary_payload["comparison_result"] = comparison
                yield streaming_svc.summary_event(summary_payload)
                yield streaming_svc.done_event()

                total_latency = perf_counter() - start_time
                routing_state = SessionService.get_llm_routing_state(llm_service)
                ReevuMetrics.get().record_request(
                    domain=MessageService.get_primary_domain(executed_plan_summary),
                    function_name=function_call.name if function_call else "",
                    status="safe_failure" if not validation.valid else "ok",
                    latency_seconds=total_latency,
                    stage="total",
                    policy_flags=list(validation.errors) if validation else [],
                    provider=actual_provider,
                    safe_failure_reason="insufficient_evidence" if not validation.valid else None,
                    routing_decisions=SessionService.derive_routing_decisions(
                        requested_provider=request.preferred_provider,
                        actual_provider=actual_provider,
                        routing_state=routing_state,
                    ),
                    retrieval_audit=retrieval_audit,
                    plan_execution_summary=executed_plan_summary,
                )

            except asyncio.CancelledError:
                logger.info("[REEVU] Stream cancelled by client")
                ReevuMetrics.get().record_request(status="error", latency_seconds=perf_counter() - start_time)
                raise
            except Exception as exc:
                logger.error("[REEVU] Streaming error: %s", exc)
                ReevuMetrics.get().record_request(status="error", latency_seconds=perf_counter() - start_time)
                yield streaming_svc.error_event(
                    str(exc),
                    safe_failure=MessageService.build_safe_failure_payload(
                        error_category="streaming_error",
                        searched=["llm_stream", "retrieved_context", "response_pipeline"],
                        missing=["successful stream completion"],
                        next_steps=[
                            "Retry the request in a few seconds.",
                            "If issue persists, narrow the query scope and retry.",
                        ],
                    ),
                )
                # Always emit done_event so the SSE client closes the connection
                # instead of hanging until server-side timeout.
                yield streaming_svc.done_event()

        return _generate()
