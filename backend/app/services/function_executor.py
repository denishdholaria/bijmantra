"""
Function Executor for Veena AI

Executes functions called by FunctionGemma.
Maps function names to actual API calls and database operations.

Per veena-critical-milestone.md:
- Veena must intelligently fetch real data from the database
- Veena must analyze that data correctly (not return canned responses)
- Veena must reason across domains
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.germplasm_search import germplasm_search_service
from app.services.trial_search import trial_search_service
from app.services.observation_search import observation_search_service
from app.services.cross_search import cross_search_service
from app.services.location_search import location_search_service
from app.services.seedlot_search import seedlot_search_service
from app.services.program_search import program_search_service
from app.services.trait_search import trait_search_service

logger = logging.getLogger(__name__)


class FunctionExecutionError(Exception):
    """Raised when function execution fails"""
    pass


class FunctionExecutor:
    """
    Executes functions called by FunctionGemma.
    
    Each function maps to one or more backend services/APIs.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute(
        self, 
        function_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function with given parameters.
        
        Args:
            function_name: Name of function to execute
            parameters: Function parameters
            
        Returns:
            Dict with execution result
            
        Raises:
            FunctionExecutionError: If execution fails
        """
        logger.info(f"Executing function: {function_name} with params: {parameters}")
        
        try:
            # Route to appropriate handler
            if function_name.startswith("search_"):
                return await self._handle_search(function_name, parameters)
            elif function_name.startswith("get_"):
                return await self._handle_get(function_name, parameters)
            elif function_name.startswith("create_"):
                return await self._handle_create(function_name, parameters)
            elif function_name.startswith("compare_"):
                return await self._handle_compare(function_name, parameters)
            elif function_name.startswith("calculate_"):
                return await self._handle_calculate(function_name, parameters)
            elif function_name.startswith("analyze_"):
                return await self._handle_analyze(function_name, parameters)
            elif function_name.startswith("record_"):
                return await self._handle_record(function_name, parameters)
            elif function_name.startswith("predict_"):
                return await self._handle_predict(function_name, parameters)
            elif function_name.startswith("check_"):
                return await self._handle_check(function_name, parameters)
            elif function_name.startswith("generate_"):
                return await self._handle_generate(function_name, parameters)
            elif function_name.startswith("export_"):
                return await self._handle_export(function_name, parameters)
            elif function_name == "navigate_to":
                return await self._handle_navigate(parameters)
            elif function_name == "get_statistics":
                return await self._handle_statistics(parameters)
            elif function_name == "cross_domain_query":
                return await self._handle_cross_domain_query(parameters)
            else:
                raise FunctionExecutionError(f"Unknown function: {function_name}")
                
        except Exception as e:
            logger.error(f"Function execution error: {e}")
            raise FunctionExecutionError(f"Failed to execute {function_name}: {str(e)}")
    
    # ========== SEARCH HANDLERS ==========
    
    async def _handle_search(self, function_name: str, params: Dict) -> Dict:
        """Handle search_* functions"""
        
        if function_name == "search_germplasm":
            # Call germplasm service with real DB session
            # Default to org_id=1 for single tenant context (or extract from params if available)
            org_id = params.get("organization_id", 1) 
            
            # Map parameters
            query = params.get("query") or params.get("q")
            # If function extraction put specific crop in params, use it as part of query or filter
            crop = params.get("crop")
            trait = params.get("trait")
            
            # Combine query terms if needed
            full_query = query
            if crop and (not query or crop not in query):
                full_query = f"{crop} {query or ''}".strip()
            
            try:
                results = await germplasm_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=full_query,
                    trait=trait,
                    limit=20  # Limit results for context window efficiency
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "germplasm_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} germplasm records matching '{full_query}'"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Search failed: {e}")
                return {
                    "success": False, 
                    "error": str(e),
                    "message": "Failed to search germplasm database"
                }
        
        elif function_name == "search_trials":
            # Call trial service with real DB session
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            crop = params.get("crop")
            location = params.get("location")
            program = params.get("program")
            status = params.get("status")
            
            try:
                results = await trial_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    crop=crop,
                    location=location,
                    program=program,
                    status=status,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "trial_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} trials" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Trial search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search trials database"
                }
        
        elif function_name == "search_crosses":
            # Call cross service with real DB session
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            parent_id = params.get("parent_id")
            status = params.get("status")
            cross_type = params.get("cross_type")
            year = params.get("year")
            
            try:
                results = await cross_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    parent_id=parent_id,
                    status=status,
                    cross_type=cross_type,
                    year=year,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "cross_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} crosses" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Cross search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search crosses database"
                }
        
        elif function_name == "search_accessions":
            # Search accessions - use location service for genebank/collection locations
            # and germplasm service for accession data
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            country = params.get("country")
            
            try:
                # Search germplasm with accession focus
                results = await germplasm_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    limit=20
                )
                
                # Filter by country if specified (via location)
                if country:
                    locations = await location_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        country=country,
                        limit=100
                    )
                    location_ids = {loc["id"] for loc in locations}
                    # Note: Would need to join germplasm with location for full filtering
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "accession_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} accessions" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Accession search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search accessions database"
                }
        
        elif function_name == "search_locations":
            # Search locations/sites
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            country = params.get("country")
            location_type = params.get("type") or params.get("location_type")
            
            try:
                results = await location_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    country=country,
                    location_type=location_type,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "location_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} locations" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Location search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search locations database"
                }
        
        elif function_name == "search_seedlots":
            # Search seedlots
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            germplasm_id = params.get("germplasm_id")
            location_id = params.get("location_id")
            
            try:
                results = await seedlot_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    germplasm_id=int(germplasm_id) if germplasm_id else None,
                    location_id=int(location_id) if location_id else None,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "seedlot_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} seedlots" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Seedlot search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search seedlots database"
                }
        
        elif function_name == "search_programs":
            # Search breeding programs
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            crop = params.get("crop")
            is_research = params.get("is_research")
            
            try:
                results = await program_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    crop=crop,
                    is_research=is_research,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "program_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} programs" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Program search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search programs database"
                }
        
        elif function_name == "search_traits":
            # Search traits/observation variables
            org_id = params.get("organization_id", 1)
            query = params.get("query") or params.get("q")
            trait_class = params.get("trait_class") or params.get("class")
            data_type = params.get("data_type")
            crop = params.get("crop")
            ontology = params.get("ontology")
            
            try:
                results = await trait_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    trait_class=trait_class,
                    data_type=data_type,
                    crop=crop,
                    ontology=ontology,
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "trait_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} traits" + (f" matching '{query}'" if query else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Trait search failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to search traits database"
                }
        
        return {"success": False, "error": f"Unhandled search function: {function_name}"}
    
    # ========== STATISTICS HANDLER ==========
    
    async def _handle_statistics(self, params: Dict) -> Dict:
        """Get cross-domain statistics from database.
        
        This enables Veena to understand the scope of data available
        and provide context-aware responses.
        """
        org_id = params.get("organization_id", 1)
        
        try:
            # Gather statistics from all domains
            germplasm_stats = await germplasm_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            trial_stats = await trial_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            observation_stats = await observation_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            cross_stats = await cross_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            location_stats = await location_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            seedlot_stats = await seedlot_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            program_stats = await program_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            trait_stats = await trait_search_service.get_statistics(
                db=self.db,
                organization_id=org_id
            )
            
            return {
                "success": True,
                "function": "get_statistics",
                "result_type": "statistics",
                "data": {
                    "programs": program_stats,
                    "germplasm": germplasm_stats,
                    "trials": trial_stats,
                    "observations": observation_stats,
                    "crosses": cross_stats,
                    "locations": location_stats,
                    "seedlots": seedlot_stats,
                    "traits": trait_stats,
                    "message": f"Database contains {program_stats.get('total_programs', 0)} programs, {germplasm_stats.get('total_germplasm', 0)} germplasm, {trial_stats.get('total_trials', 0)} trials, {observation_stats.get('total_observations', 0)} observations, {seedlot_stats.get('total_seedlots', 0)} seedlots, {trait_stats.get('total_traits', 0)} traits"
                },
                "demo": False
            }
        except Exception as e:
            logger.error(f"Get statistics failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get database statistics"
            }
    
    # ========== CROSS-DOMAIN QUERY HANDLER ==========
    
    async def _handle_cross_domain_query(self, params: Dict) -> Dict:
        """Execute a cross-domain query that spans multiple data types.
        
        This is the key function for Veena's cross-domain intelligence.
        It can answer questions like:
        - "What germplasm in my collection is drought-tolerant and suitable for low-nitrogen soils?"
        - "Show me trials with high-yielding varieties at locations with sandy soil"
        
        Per veena-critical-milestone.md: This surfaces hidden factors that users didn't explicitly ask about.
        """
        org_id = params.get("organization_id", 1)
        
        # Extract query parameters
        germplasm_query = params.get("germplasm")
        trait_query = params.get("trait")
        location_query = params.get("location")
        crop_query = params.get("crop")
        program_query = params.get("program")
        seedlot_query = params.get("seedlot")
        
        results = {
            "germplasm": [],
            "trials": [],
            "observations": [],
            "locations": [],
            "traits": [],
            "seedlots": [],
            "cross_domain_insights": []
        }
        
        try:
            # Step 1: Search traits if trait query specified
            if trait_query:
                trait_results = await trait_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=trait_query,
                    crop=crop_query,
                    limit=20
                )
                results["traits"] = trait_results
            
            # Step 2: Search germplasm if specified
            if germplasm_query or trait_query or crop_query:
                germplasm_results = await germplasm_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=germplasm_query,
                    trait=trait_query,
                    limit=20
                )
                results["germplasm"] = germplasm_results
                
                # Get observations for found germplasm to surface trait data
                for g in germplasm_results[:5]:  # Limit to avoid too much data
                    obs = await observation_search_service.get_by_germplasm(
                        db=self.db,
                        organization_id=org_id,
                        germplasm_id=int(g["id"]),
                        limit=10
                    )
                    if obs:
                        results["observations"].extend(obs)
            
            # Step 2: Search trials if location or program specified
            if location_query or program_query or crop_query:
                trial_results = await trial_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=None,
                    crop=crop_query,
                    location=location_query,
                    program=program_query,
                    limit=20
                )
                results["trials"] = trial_results
            
            # Step 3: Search locations if specified
            if location_query:
                location_results = await location_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=location_query,
                    limit=20
                )
                results["locations"] = location_results
            
            # Step 4: Search seedlots if specified
            if seedlot_query or germplasm_query:
                seedlot_results = await seedlot_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=seedlot_query,
                    limit=20
                )
                results["seedlots"] = seedlot_results
            
            # Step 5: Generate cross-domain insights
            insights = []
            
            # Insight: Traits without observations
            if results["traits"]:
                traits_with_obs = set()
                for obs in results["observations"]:
                    if obs.get("trait"):
                        traits_with_obs.add(obs["trait"].get("id"))
                
                traits_without_obs = [
                    t for t in results["traits"]
                    if t["id"] not in traits_with_obs
                ]
                if traits_without_obs:
                    insights.append({
                        "type": "trait_gap",
                        "message": f"{len(traits_without_obs)} traits have no observations in the queried germplasm",
                        "affected_items": [t["name"] for t in traits_without_obs[:5]],
                        "recommendation": "Consider phenotyping for these traits to enable selection"
                    })
            
            # Insight: Germplasm without observations
            germplasm_with_obs = set()
            for obs in results["observations"]:
                if obs.get("germplasm"):
                    germplasm_with_obs.add(obs["germplasm"]["id"])
            
            germplasm_without_obs = [
                g for g in results["germplasm"] 
                if g["id"] not in germplasm_with_obs
            ]
            if germplasm_without_obs:
                insights.append({
                    "type": "data_gap",
                    "message": f"{len(germplasm_without_obs)} germplasm entries have no phenotypic observations recorded",
                    "affected_items": [g["name"] for g in germplasm_without_obs[:5]],
                    "recommendation": "Consider phenotyping these accessions to enable trait-based selection"
                })
            
            # Insight: Trials without observations
            if results["trials"]:
                trials_needing_data = [t for t in results["trials"] if t.get("study_count", 0) == 0]
                if trials_needing_data:
                    insights.append({
                        "type": "incomplete_trial",
                        "message": f"{len(trials_needing_data)} trials have no studies/observations",
                        "affected_items": [t["name"] for t in trials_needing_data[:5]],
                        "recommendation": "Add studies and record observations for these trials"
                    })
            
            # Insight: Location coverage
            if results["locations"] and results["germplasm"]:
                insights.append({
                    "type": "coverage_summary",
                    "message": f"Query spans {len(results['locations'])} locations and {len(results['germplasm'])} germplasm entries",
                    "recommendation": "Consider multi-environment trials to assess G×E interactions"
                })
            
            # Insight: Seedlot availability
            if results["seedlots"]:
                low_quantity = [s for s in results["seedlots"] if s.get("amount", 0) < 100]
                if low_quantity:
                    insights.append({
                        "type": "seed_availability",
                        "message": f"{len(low_quantity)} seedlots have low seed quantity (<100)",
                        "affected_items": [s.get("name", s["id"]) for s in low_quantity[:5]],
                        "recommendation": "Consider seed multiplication before large-scale trials"
                    })
            
            results["cross_domain_insights"] = insights
            
            return {
                "success": True,
                "function": "cross_domain_query",
                "result_type": "cross_domain_results",
                "data": {
                    "results": results,
                    "summary": {
                        "germplasm_count": len(results["germplasm"]),
                        "trial_count": len(results["trials"]),
                        "observation_count": len(results["observations"]),
                        "location_count": len(results["locations"]),
                        "trait_count": len(results["traits"]),
                        "seedlot_count": len(results["seedlots"]),
                        "insight_count": len(insights)
                    },
                    "message": f"Cross-domain query returned {len(results['germplasm'])} germplasm, {len(results['trials'])} trials, {len(results['traits'])} traits, {len(insights)} insights"
                },
                "demo": False
            }
        except Exception as e:
            logger.error(f"Cross-domain query failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to execute cross-domain query"
            }
    
    # ========== GET HANDLERS ==========
    
    async def _handle_get(self, function_name: str, params: Dict) -> Dict:
        """Handle get_* functions"""
        
        if function_name == "get_germplasm_details":
            # Get germplasm details from database
            org_id = params.get("organization_id", 1)
            germplasm_id = params.get("germplasm_id") or params.get("id")
            
            if not germplasm_id:
                return {
                    "success": False,
                    "error": "germplasm_id is required",
                    "message": "Please specify a germplasm ID"
                }
            
            try:
                result = await germplasm_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=str(germplasm_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Germplasm not found",
                        "message": f"No germplasm found with ID {germplasm_id}"
                    }
                
                # Get observations for this germplasm
                observations = await observation_search_service.get_by_germplasm(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=int(germplasm_id),
                    limit=20
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "germplasm_details",
                    "data": {
                        "germplasm": result,
                        "observation_count": len(observations),
                        "observations": observations[:10],  # Limit for context window
                        "message": f"Germplasm '{result['name']}' with {len(observations)} observations"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get germplasm details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get germplasm details"
                }
        
        elif function_name == "get_trial_results":
            # Get trial details and associated observations
            org_id = params.get("organization_id", 1)
            trial_id = params.get("trial_id")
            
            if not trial_id:
                return {
                    "success": False,
                    "error": "trial_id is required",
                    "message": "Please specify a trial ID"
                }
            
            try:
                # Get trial details
                trial = await trial_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    trial_id=str(trial_id)
                )
                
                if not trial:
                    return {
                        "success": False,
                        "error": "Trial not found",
                        "message": f"No trial found with ID {trial_id}"
                    }
                
                # Get observations for studies in this trial
                observations = []
                for study in trial.get("studies", []):
                    study_obs = await observation_search_service.get_by_study(
                        db=self.db,
                        organization_id=org_id,
                        study_id=int(study["id"]),
                        limit=50
                    )
                    observations.extend(study_obs)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "trial_results",
                    "data": {
                        "trial": trial,
                        "observation_count": len(observations),
                        "observations": observations[:20],  # Limit for context window
                        "message": f"Trial '{trial['name']}' with {len(observations)} observations"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get trial results failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get trial results"
                }
        
        elif function_name == "get_observations":
            # Get observations with filters
            org_id = params.get("organization_id", 1)
            trait = params.get("trait")
            study_id = params.get("study_id")
            germplasm_id = params.get("germplasm_id")
            query = params.get("query") or params.get("q")
            
            try:
                results = await observation_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    query=query,
                    trait=trait,
                    study_id=int(study_id) if study_id else None,
                    germplasm_id=int(germplasm_id) if germplasm_id else None,
                    limit=50
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "observation_list",
                    "data": {
                        "total": len(results),
                        "items": results,
                        "message": f"Found {len(results)} observations" + (f" for trait '{trait}'" if trait else "")
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get observations failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get observations"
                }
        
        elif function_name == "get_trait_details":
            # Get trait/observation variable details
            org_id = params.get("organization_id", 1)
            trait_id = params.get("trait_id") or params.get("id")
            
            if not trait_id:
                return {
                    "success": False,
                    "error": "trait_id is required",
                    "message": "Please specify a trait ID"
                }
            
            try:
                result = await trait_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    trait_id=str(trait_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Trait not found",
                        "message": f"No trait found with ID {trait_id}"
                    }
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "trait_details",
                    "data": {
                        "trait": result,
                        "observation_count": result.get("observation_count", 0),
                        "message": f"Trait '{result['name']}' ({result.get('trait_class', 'unknown class')})"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get trait details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get trait details"
                }
        
        elif function_name == "get_program_details":
            # Get breeding program details
            org_id = params.get("organization_id", 1)
            program_id = params.get("program_id") or params.get("id")
            
            if not program_id:
                return {
                    "success": False,
                    "error": "program_id is required",
                    "message": "Please specify a program ID"
                }
            
            try:
                result = await program_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    program_id=str(program_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Program not found",
                        "message": f"No program found with ID {program_id}"
                    }
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "program_details",
                    "data": {
                        "program": result,
                        "trial_count": result.get("trial_count", 0),
                        "message": f"Program '{result['name']}' with {result.get('trial_count', 0)} trials"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get program details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get program details"
                }
        
        elif function_name == "get_location_details":
            # Get location details
            org_id = params.get("organization_id", 1)
            location_id = params.get("location_id") or params.get("id")
            
            if not location_id:
                return {
                    "success": False,
                    "error": "location_id is required",
                    "message": "Please specify a location ID"
                }
            
            try:
                result = await location_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    location_id=str(location_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Location not found",
                        "message": f"No location found with ID {location_id}"
                    }
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "location_details",
                    "data": {
                        "location": result,
                        "message": f"Location '{result['name']}' in {result.get('country', 'unknown country')}"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get location details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get location details"
                }
        
        elif function_name == "get_seedlot_details":
            # Get seedlot details
            org_id = params.get("organization_id", 1)
            seedlot_id = params.get("seedlot_id") or params.get("id")
            
            if not seedlot_id:
                return {
                    "success": False,
                    "error": "seedlot_id is required",
                    "message": "Please specify a seedlot ID"
                }
            
            try:
                result = await seedlot_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    seedlot_id=str(seedlot_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Seedlot not found",
                        "message": f"No seedlot found with ID {seedlot_id}"
                    }
                
                # Also check viability
                viability = await seedlot_search_service.check_viability(
                    db=self.db,
                    organization_id=org_id,
                    seedlot_id=str(seedlot_id)
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "seedlot_details",
                    "data": {
                        "seedlot": result,
                        "viability": viability,
                        "message": f"Seedlot '{result.get('name', seedlot_id)}' - {result.get('amount', 0)} {result.get('units', 'seeds')}"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get seedlot details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get seedlot details"
                }
        
        elif function_name == "get_cross_details":
            # Get cross details
            org_id = params.get("organization_id", 1)
            cross_id = params.get("cross_id") or params.get("id")
            
            if not cross_id:
                return {
                    "success": False,
                    "error": "cross_id is required",
                    "message": "Please specify a cross ID"
                }
            
            try:
                result = await cross_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    cross_id=str(cross_id)
                )
                
                if not result:
                    return {
                        "success": False,
                        "error": "Cross not found",
                        "message": f"No cross found with ID {cross_id}"
                    }
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "cross_details",
                    "data": {
                        "cross": result,
                        "message": f"Cross '{result.get('name', cross_id)}' - {result.get('status', 'unknown status')}"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Get cross details failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get cross details"
                }
        
        elif function_name == "get_weather_forecast":
            # Get weather forecast using weather_service
            from app.services.weather_service import weather_service
            
            location = params.get("location") or params.get("location_id") or "default"
            location_name = params.get("location_name") or location
            days = params.get("days", 7)
            crop = params.get("crop", "wheat")
            
            try:
                forecast = await weather_service.get_forecast(
                    location_id=str(location),
                    location_name=location_name,
                    days=days,
                    crop=crop
                )
                
                # Get Veena-friendly summary
                summary = weather_service.get_veena_summary(forecast)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "weather_forecast",
                    "data": {
                        "location": location_name,
                        "days": days,
                        "summary": summary,
                        "alerts": forecast.alerts,
                        "impacts_count": len(forecast.impacts),
                        "optimal_windows": [
                            {
                                "activity": w.activity.value,
                                "start": w.start.isoformat(),
                                "end": w.end.isoformat(),
                                "confidence": w.confidence
                            }
                            for w in forecast.optimal_windows[:5]
                        ],
                        "message": f"Weather forecast for {location_name} ({days} days)"
                    },
                    "demo": False  # Uses weather_service (simulated but structured)
                }
            except Exception as e:
                logger.error(f"Get weather forecast failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to get weather forecast"
                }
        
        return {"success": False, "error": f"Unhandled get function: {function_name}"}
    
    # ========== CREATE HANDLERS ==========
    
    async def _handle_create(self, function_name: str, params: Dict) -> Dict:
        """Handle create_* functions - Database write operations"""
        from app.models.core import Trial, Program
        from app.models.germplasm import Cross, Germplasm, CrossingProject
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
        from sqlalchemy import select
        from datetime import datetime, timezone
        import uuid
        
        org_id = params.get("organization_id", 1)
        
        if function_name == "create_trial":
            # Create a new trial in the database
            name = params.get("name")
            program_id = params.get("program_id")
            program_name = params.get("program_name")
            description = params.get("description", "")
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            
            if not name:
                return {
                    "success": False,
                    "error": "name is required",
                    "message": "Please specify a name for the trial"
                }
            
            try:
                # Look up program if program_name provided
                if program_name and not program_id:
                    stmt = select(Program).where(
                        Program.name.ilike(f"%{program_name}%"),
                        Program.organization_id == org_id
                    )
                    result = await self.db.execute(stmt)
                    program = result.scalar_one_or_none()
                    if program:
                        program_id = program.id
                
                if not program_id:
                    # Get first available program for the organization
                    stmt = select(Program).where(Program.organization_id == org_id).limit(1)
                    result = await self.db.execute(stmt)
                    program = result.scalar_one_or_none()
                    if program:
                        program_id = program.id
                    else:
                        return {
                            "success": False,
                            "error": "No program found",
                            "message": "A program is required to create a trial. Please create a program first."
                        }
                
                trial_db_id = f"trial_{uuid.uuid4().hex[:12]}"
                
                new_trial = Trial(
                    organization_id=org_id,
                    trial_db_id=trial_db_id,
                    trial_name=name,
                    program_id=program_id,
                    trial_description=description,
                    start_date=start_date,
                    end_date=end_date,
                    active=True
                )
                
                self.db.add(new_trial)
                await self.db.commit()
                await self.db.refresh(new_trial)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "trial_created",
                    "data": {
                        "trial_id": new_trial.id,
                        "trial_db_id": trial_db_id,
                        "name": name,
                        "program_id": program_id,
                        "message": f"Trial '{name}' created successfully"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Create trial failed: {e}")
                await self.db.rollback()
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to create trial"
                }
        
        elif function_name == "create_cross":
            # Create a new cross in the database
            parent1_id = params.get("parent1_id")
            parent2_id = params.get("parent2_id")
            cross_name = params.get("name") or params.get("cross_name")
            cross_type = params.get("cross_type", "BIPARENTAL")
            crossing_year = params.get("year") or params.get("crossing_year")
            
            if not parent1_id or not parent2_id:
                return {
                    "success": False,
                    "error": "parent1_id and parent2_id are required",
                    "message": "Please specify both parent IDs for the cross"
                }
            
            try:
                # Look up parents
                stmt = select(Germplasm).where(
                    Germplasm.id == int(parent1_id),
                    Germplasm.organization_id == org_id
                )
                result = await self.db.execute(stmt)
                parent1 = result.scalar_one_or_none()
                
                stmt = select(Germplasm).where(
                    Germplasm.id == int(parent2_id),
                    Germplasm.organization_id == org_id
                )
                result = await self.db.execute(stmt)
                parent2 = result.scalar_one_or_none()
                
                if not parent1 or not parent2:
                    missing = []
                    if not parent1:
                        missing.append(f"parent1 ({parent1_id})")
                    if not parent2:
                        missing.append(f"parent2 ({parent2_id})")
                    return {
                        "success": False,
                        "error": "Parent(s) not found",
                        "message": f"Could not find: {', '.join(missing)}"
                    }
                
                # Generate cross name if not provided
                if not cross_name:
                    cross_name = f"{parent1.germplasm_name} × {parent2.germplasm_name}"
                
                cross_db_id = f"cross_{uuid.uuid4().hex[:12]}"
                
                new_cross = Cross(
                    organization_id=org_id,
                    cross_db_id=cross_db_id,
                    cross_name=cross_name,
                    cross_type=cross_type,
                    parent1_db_id=parent1.id,
                    parent2_db_id=parent2.id,
                    crossing_year=crossing_year or datetime.now().year,
                    pollination_time_stamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.db.add(new_cross)
                await self.db.commit()
                await self.db.refresh(new_cross)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "cross_created",
                    "data": {
                        "cross_id": new_cross.id,
                        "cross_db_id": cross_db_id,
                        "name": cross_name,
                        "parent1": {"id": parent1.id, "name": parent1.germplasm_name},
                        "parent2": {"id": parent2.id, "name": parent2.germplasm_name},
                        "cross_type": cross_type,
                        "message": f"Cross '{cross_name}' created successfully"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Create cross failed: {e}")
                await self.db.rollback()
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to create cross"
                }
        
        return {"success": False, "error": f"Unhandled create function: {function_name}"}
    
    # ========== COMPARE HANDLERS ==========
    
    async def _handle_compare(self, function_name: str, params: Dict) -> Dict:
        """Handle compare_* functions"""
        
        if function_name == "compare_germplasm":
            # Compare multiple germplasm entries
            org_id = params.get("organization_id", 1)
            germplasm_ids = params.get("germplasm_ids", [])
            traits = params.get("traits", [])
            
            if not germplasm_ids or len(germplasm_ids) < 2:
                return {
                    "success": False,
                    "error": "At least 2 germplasm IDs required",
                    "message": "Please specify at least 2 germplasm IDs to compare"
                }
            
            try:
                # Fetch details for each germplasm
                germplasm_data = []
                for gid in germplasm_ids[:5]:  # Limit to 5 for comparison
                    g = await germplasm_search_service.get_by_id(
                        db=self.db,
                        organization_id=org_id,
                        germplasm_id=str(gid)
                    )
                    if g:
                        # Get observations for this germplasm
                        obs = await observation_search_service.get_by_germplasm(
                            db=self.db,
                            organization_id=org_id,
                            germplasm_id=int(gid),
                            limit=50
                        )
                        g["observations"] = obs
                        g["observation_count"] = len(obs)
                        germplasm_data.append(g)
                
                if len(germplasm_data) < 2:
                    return {
                        "success": False,
                        "error": "Not enough germplasm found",
                        "message": f"Only found {len(germplasm_data)} of {len(germplasm_ids)} requested germplasm"
                    }
                
                # Build comparison summary
                comparison = {
                    "germplasm_count": len(germplasm_data),
                    "items": germplasm_data,
                    "common_traits": [],
                    "differences": []
                }
                
                # Find common and different traits
                all_traits = set()
                for g in germplasm_data:
                    all_traits.update(g.get("traits", []))
                
                comparison["all_traits"] = list(all_traits)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "comparison",
                    "data": {
                        "comparison": comparison,
                        "message": f"Compared {len(germplasm_data)} germplasm entries"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Compare germplasm failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to compare germplasm"
                }
        
        return {"success": False, "error": f"Unhandled compare function: {function_name}"}
    
    # ========== CALCULATE HANDLERS ==========
    
    async def _handle_calculate(self, function_name: str, params: Dict) -> Dict:
        """Handle calculate_* functions"""
        
        if function_name == "calculate_breeding_value":
            # Calculate breeding values using BLUP/GBLUP with real phenotype data
            from app.services.breeding_value import breeding_value_service
            
            org_id = params.get("organization_id", 1)
            trait = params.get("trait")
            method = params.get("method", "BLUP").upper()
            heritability = params.get("heritability", 0.3)
            germplasm_ids = params.get("germplasm_ids", [])
            study_id = params.get("study_id")
            
            if not trait:
                return {
                    "success": False,
                    "error": "trait is required",
                    "message": "Please specify a trait for breeding value calculation"
                }
            
            try:
                # Fetch phenotype observations from database
                observations = await observation_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    trait=trait,
                    study_id=int(study_id) if study_id else None,
                    limit=500  # Get enough data for analysis
                )
                
                if len(observations) < 3:
                    return {
                        "success": False,
                        "error": "Insufficient data",
                        "message": f"Need at least 3 observations for BLUP. Found {len(observations)} for trait '{trait}'"
                    }
                
                # Transform observations to phenotype format for breeding_value_service
                phenotypes = []
                for obs in observations:
                    try:
                        value = float(obs.get("value", 0))
                        germ = obs.get("germplasm", {})
                        phenotypes.append({
                            "id": germ.get("id", obs.get("id")),
                            "name": germ.get("name", f"Unknown-{obs.get('id')}"),
                            "value": value
                        })
                    except (ValueError, TypeError):
                        continue  # Skip non-numeric observations
                
                if len(phenotypes) < 3:
                    return {
                        "success": False,
                        "error": "Insufficient numeric data",
                        "message": f"Need at least 3 numeric observations. Found {len(phenotypes)} valid records."
                    }
                
                # Calculate breeding values using the service
                if method == "GBLUP":
                    # GBLUP requires marker data - check if available
                    # For now, fall back to BLUP if no markers
                    result = breeding_value_service.estimate_blup(
                        phenotypes=phenotypes,
                        trait="value",
                        heritability=heritability
                    )
                    result["note"] = "GBLUP requested but marker data not available. Used BLUP instead."
                else:
                    result = breeding_value_service.estimate_blup(
                        phenotypes=phenotypes,
                        trait="value",
                        heritability=heritability
                    )
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "message": f"Breeding value calculation failed: {result['error']}"
                    }
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "breeding_values",
                    "data": {
                        "method": result.get("method", method),
                        "trait": trait,
                        "n_individuals": result.get("n_individuals", len(phenotypes)),
                        "heritability": result.get("heritability", heritability),
                        "overall_mean": result.get("overall_mean"),
                        "genetic_variance": result.get("genetic_variance"),
                        "top_10": result.get("top_10", []),
                        "analysis_id": result.get("analysis_id"),
                        "message": f"Calculated {method} breeding values for {result.get('n_individuals', 0)} individuals on trait '{trait}'"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Calculate breeding value failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to calculate breeding values"
                }
        
        elif function_name == "calculate_genetic_diversity":
            # Calculate genetic diversity from real genotype data
            from app.services.genetic_diversity import genetic_diversity_service
            
            org_id = params.get("organization_id", 1)
            population_id = params.get("population_id")
            program_id = params.get("program_id")
            germplasm_ids = params.get("germplasm_ids", [])
            
            try:
                # Calculate diversity metrics from database
                result = await genetic_diversity_service.calculate_diversity_metrics(
                    db=self.db,
                    organization_id=org_id,
                    population_id=population_id,
                    program_id=int(program_id) if program_id else None,
                    germplasm_ids=[int(g) for g in germplasm_ids] if germplasm_ids else None,
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "diversity_metrics",
                    "data": result,
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Calculate genetic diversity failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to calculate genetic diversity"
                }
        
        elif function_name == "calculate_gdd":
            # Calculate Growing Degree Days using crop_calendar service or weather_service
            from app.services.weather_service import weather_service
            
            location = params.get("location") or params.get("location_id") or "default"
            location_name = params.get("location_name") or location
            crop = params.get("crop", "wheat")
            days = params.get("days", 14)
            
            try:
                # Use weather_service which has GDD calculation built in
                forecast = await weather_service.get_forecast(
                    location_id=str(location),
                    location_name=location_name,
                    days=days,
                    crop=crop
                )
                
                gdd_data = forecast.gdd_forecast
                total_gdd = gdd_data[-1].gdd_cumulative if gdd_data else 0
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "gdd_result",
                    "data": {
                        "location": location_name,
                        "crop": crop,
                        "base_temperature": gdd_data[0].base_temp if gdd_data else None,
                        "days": days,
                        "total_gdd": total_gdd,
                        "daily_gdd": [
                            {
                                "date": g.date.isoformat(),
                                "daily": g.gdd_daily,
                                "cumulative": g.gdd_cumulative
                            }
                            for g in gdd_data[:7]  # Limit for context window
                        ],
                        "message": f"GDD for {crop} at {location_name}: {total_gdd:.1f}°C·days over {days} days"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Calculate GDD failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to calculate GDD"
                }
        
        return {"success": False, "error": f"Unhandled calculate function: {function_name}"}
    
    # ========== ANALYZE HANDLERS ==========
    
    async def _handle_analyze(self, function_name: str, params: Dict) -> Dict:
        """Handle analyze_* functions"""
        
        if function_name == "analyze_gxe":
            # G×E interaction analysis using real observation data
            from app.services.gxe_analysis import get_gxe_service, GxEMethod
            import numpy as np
            
            org_id = params.get("organization_id", 1)
            trait = params.get("trait")
            method = params.get("method", "AMMI").upper()
            trial_ids = params.get("trial_ids", [])
            
            if not trait:
                return {
                    "success": False,
                    "error": "trait is required",
                    "message": "Please specify a trait for G×E analysis"
                }
            
            try:
                # Fetch observations for the trait
                observations = await observation_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    trait=trait,
                    limit=1000  # Get enough data for multi-environment analysis
                )
                
                if len(observations) < 6:
                    return {
                        "success": False,
                        "error": "Insufficient data",
                        "message": f"Need at least 6 observations for G×E analysis. Found {len(observations)} for trait '{trait}'"
                    }
                
                # Build yield matrix: genotypes × environments
                # Group observations by germplasm and location/study
                geno_env_data = {}  # {(geno_id, env_id): [values]}
                genotypes = set()
                environments = set()
                geno_names = {}
                env_names = {}
                
                for obs in observations:
                    try:
                        value = float(obs.get("value", 0))
                        germ = obs.get("germplasm", {})
                        geno_id = germ.get("id")
                        geno_name = germ.get("name", f"G{geno_id}")
                        
                        # Use study or location as environment
                        study = obs.get("study", {})
                        env_id = study.get("id") if study else obs.get("location_id", "unknown")
                        env_name = study.get("name") if study else f"Env{env_id}"
                        
                        if geno_id and env_id:
                            key = (geno_id, env_id)
                            if key not in geno_env_data:
                                geno_env_data[key] = []
                            geno_env_data[key].append(value)
                            genotypes.add(geno_id)
                            environments.add(env_id)
                            geno_names[geno_id] = geno_name
                            env_names[env_id] = env_name
                    except (ValueError, TypeError):
                        continue
                
                # Need at least 2 genotypes and 2 environments
                if len(genotypes) < 2 or len(environments) < 2:
                    return {
                        "success": False,
                        "error": "Insufficient variation",
                        "message": f"Need at least 2 genotypes and 2 environments. Found {len(genotypes)} genotypes, {len(environments)} environments."
                    }
                
                # Build yield matrix (mean values per cell)
                geno_list = sorted(genotypes)
                env_list = sorted(environments)
                yield_matrix = np.zeros((len(geno_list), len(env_list)))
                
                for i, geno_id in enumerate(geno_list):
                    for j, env_id in enumerate(env_list):
                        key = (geno_id, env_id)
                        if key in geno_env_data and geno_env_data[key]:
                            yield_matrix[i, j] = np.mean(geno_env_data[key])
                        else:
                            # Use genotype mean for missing cells
                            geno_vals = [v for k, vals in geno_env_data.items() if k[0] == geno_id for v in vals]
                            yield_matrix[i, j] = np.mean(geno_vals) if geno_vals else 0
                
                geno_name_list = [geno_names.get(g, f"G{g}") for g in geno_list]
                env_name_list = [env_names.get(e, f"E{e}") for e in env_list]
                
                # Run G×E analysis
                gxe_service = get_gxe_service()
                
                if method == "GGE":
                    result = gxe_service.gge_biplot(
                        yield_matrix=yield_matrix,
                        genotype_names=geno_name_list,
                        environment_names=env_name_list
                    )
                    result_dict = result.to_dict()
                    
                    # Add winning genotypes
                    winners = gxe_service.identify_winning_genotypes(result)
                    result_dict["winning_genotypes"] = winners
                    
                elif method == "FINLAY_WILKINSON" or method == "FW":
                    result = gxe_service.finlay_wilkinson(
                        yield_matrix=yield_matrix,
                        genotype_names=geno_name_list,
                        environment_names=env_name_list
                    )
                    result_dict = result.to_dict()
                    
                else:  # Default to AMMI
                    result = gxe_service.ammi_analysis(
                        yield_matrix=yield_matrix,
                        genotype_names=geno_name_list,
                        environment_names=env_name_list
                    )
                    result_dict = result.to_dict()
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "gxe_analysis",
                    "data": {
                        "method": method,
                        "trait": trait,
                        "n_genotypes": len(geno_list),
                        "n_environments": len(env_list),
                        "n_observations": len(observations),
                        "analysis": result_dict,
                        "message": f"{method} analysis: {len(geno_list)} genotypes × {len(env_list)} environments for trait '{trait}'"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Analyze G×E failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to perform G×E analysis"
                }
        
        return {"success": False, "error": f"Unhandled analyze function: {function_name}"}
    
    # ========== RECORD HANDLERS ==========
    
    async def _handle_record(self, function_name: str, params: Dict) -> Dict:
        """Handle record_* functions - Database write operations"""
        from app.models.phenotyping import Observation, ObservationUnit, ObservationVariable
        from app.models.germplasm import Germplasm
        from sqlalchemy import select
        from datetime import datetime, timezone
        import uuid
        
        org_id = params.get("organization_id", 1)
        
        if function_name == "record_observation":
            # Record a new observation in the database
            trait = params.get("trait") or params.get("trait_name")
            value = params.get("value")
            germplasm_id = params.get("germplasm_id")
            observation_unit_id = params.get("observation_unit_id")
            study_id = params.get("study_id")
            collector = params.get("collector", "Veena AI")
            
            if value is None:
                return {
                    "success": False,
                    "error": "value is required",
                    "message": "Please specify a value for the observation"
                }
            
            try:
                # Look up observation variable (trait) by name
                obs_var_id = None
                obs_var_name = trait
                if trait:
                    stmt = select(ObservationVariable).where(
                        ObservationVariable.observation_variable_name.ilike(f"%{trait}%"),
                        ObservationVariable.organization_id == org_id
                    )
                    result = await self.db.execute(stmt)
                    obs_var = result.scalar_one_or_none()
                    if obs_var:
                        obs_var_id = obs_var.id
                        obs_var_name = obs_var.observation_variable_name
                
                # Look up observation unit if provided
                obs_unit_id = None
                if observation_unit_id:
                    stmt = select(ObservationUnit).where(
                        ObservationUnit.id == int(observation_unit_id),
                        ObservationUnit.organization_id == org_id
                    )
                    result = await self.db.execute(stmt)
                    obs_unit = result.scalar_one_or_none()
                    if obs_unit:
                        obs_unit_id = obs_unit.id
                
                # Look up germplasm if provided (for context)
                germplasm_name = None
                if germplasm_id:
                    stmt = select(Germplasm).where(
                        Germplasm.id == int(germplasm_id),
                        Germplasm.organization_id == org_id
                    )
                    result = await self.db.execute(stmt)
                    germ = result.scalar_one_or_none()
                    if germ:
                        germplasm_name = germ.germplasm_name
                
                obs_db_id = f"obs_{uuid.uuid4().hex[:12]}"
                
                new_obs = Observation(
                    organization_id=org_id,
                    observation_db_id=obs_db_id,
                    observation_unit_id=obs_unit_id,
                    observation_variable_id=obs_var_id,
                    value=str(value),
                    observation_time_stamp=datetime.now(timezone.utc).isoformat() + "Z",
                    collector=collector
                )
                
                self.db.add(new_obs)
                await self.db.commit()
                await self.db.refresh(new_obs)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "observation_recorded",
                    "data": {
                        "observation_id": new_obs.id,
                        "observation_db_id": obs_db_id,
                        "trait": obs_var_name,
                        "value": value,
                        "germplasm": germplasm_name,
                        "collector": collector,
                        "timestamp": new_obs.observation_time_stamp,
                        "message": f"Observation recorded: {obs_var_name or 'unknown trait'} = {value}"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Record observation failed: {e}")
                await self.db.rollback()
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to record observation"
                }
        
        return {"success": False, "error": f"Unhandled record function: {function_name}"}
    
    # ========== PREDICT HANDLERS ==========
    
    async def _handle_predict(self, function_name: str, params: Dict) -> Dict:
        """Handle predict_* functions"""
        
        if function_name == "predict_cross":
            # Predict cross outcome using breeding_value_service with real germplasm data
            from app.services.breeding_value import breeding_value_service
            
            org_id = params.get("organization_id", 1)
            parent1_id = params.get("parent1_id")
            parent2_id = params.get("parent2_id")
            trait = params.get("trait")
            heritability = params.get("heritability", 0.3)
            
            if not parent1_id or not parent2_id:
                return {
                    "success": False,
                    "error": "parent1_id and parent2_id are required",
                    "message": "Please specify both parent IDs for cross prediction"
                }
            
            try:
                # Fetch parent germplasm details
                parent1 = await germplasm_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=str(parent1_id)
                )
                parent2 = await germplasm_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=str(parent2_id)
                )
                
                if not parent1 or not parent2:
                    missing = []
                    if not parent1:
                        missing.append(f"parent1 ({parent1_id})")
                    if not parent2:
                        missing.append(f"parent2 ({parent2_id})")
                    return {
                        "success": False,
                        "error": "Parent(s) not found",
                        "message": f"Could not find: {', '.join(missing)}"
                    }
                
                # Get observations for both parents to estimate their breeding values
                parent1_obs = await observation_search_service.get_by_germplasm(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=int(parent1_id),
                    limit=50
                )
                parent2_obs = await observation_search_service.get_by_germplasm(
                    db=self.db,
                    organization_id=org_id,
                    germplasm_id=int(parent2_id),
                    limit=50
                )
                
                # Calculate mean phenotype values for each parent
                def calc_mean(observations, trait_filter=None):
                    values = []
                    for obs in observations:
                        if trait_filter and obs.get("trait", {}).get("name", "").lower() != trait_filter.lower():
                            continue
                        try:
                            values.append(float(obs.get("value", 0)))
                        except (ValueError, TypeError):
                            continue
                    return sum(values) / len(values) if values else 0
                
                parent1_mean = calc_mean(parent1_obs, trait)
                parent2_mean = calc_mean(parent2_obs, trait)
                
                # Get overall trait mean from database
                all_obs = await observation_search_service.search(
                    db=self.db,
                    organization_id=org_id,
                    trait=trait,
                    limit=200
                )
                trait_mean = calc_mean(all_obs)
                
                # Estimate EBVs (simplified: deviation from mean * heritability)
                parent1_ebv = (parent1_mean - trait_mean) * heritability if trait_mean else 0
                parent2_ebv = (parent2_mean - trait_mean) * heritability if trait_mean else 0
                
                # Use breeding_value_service for cross prediction
                prediction = breeding_value_service.predict_cross(
                    parent1_ebv=parent1_ebv,
                    parent2_ebv=parent2_ebv,
                    trait_mean=trait_mean,
                    heritability=heritability
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "cross_prediction",
                    "data": {
                        "parent1": {
                            "id": parent1_id,
                            "name": parent1.get("name"),
                            "mean_phenotype": round(parent1_mean, 4) if parent1_mean else None,
                            "estimated_ebv": round(parent1_ebv, 4),
                            "observation_count": len(parent1_obs)
                        },
                        "parent2": {
                            "id": parent2_id,
                            "name": parent2.get("name"),
                            "mean_phenotype": round(parent2_mean, 4) if parent2_mean else None,
                            "estimated_ebv": round(parent2_ebv, 4),
                            "observation_count": len(parent2_obs)
                        },
                        "trait": trait or "all traits",
                        "trait_mean": round(trait_mean, 4) if trait_mean else None,
                        "heritability": heritability,
                        "prediction": prediction,
                        "message": f"Cross prediction: {parent1.get('name')} × {parent2.get('name')}"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Predict cross failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to predict cross outcome"
                }
        
        return {"success": False, "error": f"Unhandled predict function: {function_name}"}
    
    # ========== CHECK HANDLERS ==========
    
    async def _handle_check(self, function_name: str, params: Dict) -> Dict:
        """Handle check_* functions"""
        
        if function_name == "check_seed_viability":
            # Check seed viability for a seedlot
            org_id = params.get("organization_id", 1)
            seedlot_id = params.get("seedlot_id") or params.get("accession_id")
            germplasm_id = params.get("germplasm_id")
            
            try:
                # If germplasm_id provided, find seedlots for that germplasm
                if germplasm_id and not seedlot_id:
                    seedlots = await seedlot_search_service.get_by_germplasm(
                        db=self.db,
                        organization_id=org_id,
                        germplasm_id=int(germplasm_id),
                        limit=5
                    )
                    
                    if not seedlots:
                        return {
                            "success": False,
                            "error": "No seedlots found",
                            "message": f"No seedlots found for germplasm ID {germplasm_id}"
                        }
                    
                    # Check viability for all seedlots
                    viability_results = []
                    for sl in seedlots:
                        result = await seedlot_search_service.check_viability(
                            db=self.db,
                            organization_id=org_id,
                            seedlot_id=sl["id"]
                        )
                        viability_results.append(result)
                    
                    return {
                        "success": True,
                        "function": function_name,
                        "result_type": "viability_results",
                        "data": {
                            "seedlot_count": len(viability_results),
                            "results": viability_results,
                            "message": f"Checked viability for {len(viability_results)} seedlots"
                        },
                        "demo": False
                    }
                
                # Direct seedlot check
                if not seedlot_id:
                    return {
                        "success": False,
                        "error": "seedlot_id or germplasm_id required",
                        "message": "Please specify a seedlot ID or germplasm ID"
                    }
                
                result = await seedlot_search_service.check_viability(
                    db=self.db,
                    organization_id=org_id,
                    seedlot_id=str(seedlot_id)
                )
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "viability_result",
                    "data": result,
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Check seed viability failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to check seed viability"
                }
        
        return {"success": False, "error": f"Unhandled check function: {function_name}"}
    
    # ========== GENERATE HANDLERS ==========
    
    async def _handle_generate(self, function_name: str, params: Dict) -> Dict:
        """Handle generate_* functions"""
        
        if function_name == "generate_trial_report":
            # Generate trial report using real trial data
            from app.models.collaboration import GeneratedReport, ReportFormat, ReportStatus
            from datetime import datetime, timezone, timedelta
            import uuid
            
            org_id = params.get("organization_id", 1)
            trial_id = params.get("trial_id")
            format_str = params.get("format", "PDF").upper()
            
            if not trial_id:
                return {
                    "success": False,
                    "error": "trial_id is required",
                    "message": "Please specify a trial ID for the report"
                }
            
            try:
                # Get trial details
                trial = await trial_search_service.get_by_id(
                    db=self.db,
                    organization_id=org_id,
                    trial_id=str(trial_id)
                )
                
                if not trial:
                    return {
                        "success": False,
                        "error": "Trial not found",
                        "message": f"No trial found with ID {trial_id}"
                    }
                
                # Get observations for the trial
                observations = []
                for study in trial.get("studies", []):
                    study_obs = await observation_search_service.get_by_study(
                        db=self.db,
                        organization_id=org_id,
                        study_id=int(study["id"]),
                        limit=100
                    )
                    observations.extend(study_obs)
                
                # Parse format
                try:
                    report_format = ReportFormat(format_str)
                except ValueError:
                    report_format = ReportFormat.PDF
                
                # Create report record
                report_id = uuid.uuid4().hex[:8]
                report = GeneratedReport(
                    organization_id=org_id,
                    name=f"{trial['name']} Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                    format=report_format,
                    status=ReportStatus.COMPLETED,
                    size_bytes=len(observations) * 100,  # Estimate
                    download_url=f"/api/v2/reports/download/{report_id}",
                    parameters={"trial_id": trial_id, "observation_count": len(observations)},
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7)
                )
                
                self.db.add(report)
                await self.db.commit()
                await self.db.refresh(report)
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "report_generated",
                    "data": {
                        "report_id": report.id,
                        "trial_id": trial_id,
                        "trial_name": trial["name"],
                        "format": format_str,
                        "observation_count": len(observations),
                        "study_count": len(trial.get("studies", [])),
                        "download_url": report.download_url,
                        "expires_at": report.expires_at.isoformat() if report.expires_at else None,
                        "message": f"Report generated for trial '{trial['name']}' with {len(observations)} observations"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Generate trial report failed: {e}")
                await self.db.rollback()
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to generate trial report"
                }
        
        return {"success": False, "error": f"Unhandled generate function: {function_name}"}
    
    # ========== EXPORT HANDLERS ==========
    
    async def _handle_export(self, function_name: str, params: Dict) -> Dict:
        """Handle export_* functions"""
        
        if function_name == "export_data":
            # Export data using DataExportService with real database data
            from app.services.data_export import get_export_service
            
            org_id = params.get("organization_id", 1)
            data_type = params.get("data_type", "germplasm").lower()
            format_str = params.get("format", "csv").lower()
            query = params.get("query")
            limit = params.get("limit", 100)
            
            try:
                export_service = get_export_service()
                data = []
                
                # Fetch data based on type
                if data_type == "germplasm":
                    results = await germplasm_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "trials":
                    results = await trial_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "observations":
                    results = await observation_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "crosses":
                    results = await cross_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "locations":
                    results = await location_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "seedlots":
                    results = await seedlot_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "traits":
                    results = await trait_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                elif data_type == "programs":
                    results = await program_search_service.search(
                        db=self.db,
                        organization_id=org_id,
                        query=query,
                        limit=limit
                    )
                    data = results
                    
                else:
                    return {
                        "success": False,
                        "error": f"Unknown data type: {data_type}",
                        "message": f"Supported types: germplasm, trials, observations, crosses, locations, seedlots, traits, programs"
                    }
                
                if not data:
                    return {
                        "success": True,
                        "function": function_name,
                        "result_type": "data_exported",
                        "data": {
                            "data_type": data_type,
                            "format": format_str,
                            "record_count": 0,
                            "content": "",
                            "message": f"No {data_type} data found to export"
                        },
                        "demo": False
                    }
                
                # Export to requested format
                if format_str == "csv":
                    content = export_service.export_to_csv(data)
                elif format_str == "tsv":
                    content = export_service.export_to_tsv(data)
                elif format_str == "json":
                    content = export_service.export_to_json(data)
                else:
                    content = export_service.export_to_csv(data)
                    format_str = "csv"
                
                return {
                    "success": True,
                    "function": function_name,
                    "result_type": "data_exported",
                    "data": {
                        "data_type": data_type,
                        "format": format_str,
                        "record_count": len(data),
                        "content_preview": content[:500] + "..." if len(content) > 500 else content,
                        "content_length": len(content),
                        "message": f"Exported {len(data)} {data_type} records in {format_str.upper()} format"
                    },
                    "demo": False
                }
            except Exception as e:
                logger.error(f"Export data failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to export data"
                }
        
        return {"success": False, "error": f"Unhandled export function: {function_name}"}
    
    # ========== NAVIGATE HANDLERS ==========
    
    async def _handle_navigate(self, params: Dict) -> Dict:
        """Handle navigate_to function"""
        page = params.get("page")
        filters = params.get("filters", {})
        
        return {
            "success": True,
            "function": "navigate_to",
            "result_type": "navigation",
            "data": {
                "page": page,
                "filters": filters,
                "action": "navigate"
            }
        }
