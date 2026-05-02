/**
 * Zod schemas for API response validation.
 *
 * These are used with the optional `schema` parameter on ApiClientCore.request()
 * to add runtime validation to the highest-risk response shapes.
 *
 * Adoption strategy:
 *   - Start with auth and workspace preferences (used on every session).
 *   - Add schemas to other services incrementally as they are touched.
 *   - Validation is non-blocking: failures are logged at WARN level and the
 *     raw parsed value is returned, so existing callers are never broken.
 *
 * Usage:
 *   import { LoginResponseSchema } from '@/lib/api/core/schemas';
 *   const data = await this.client.post('/api/auth/login', body, {}, LoginResponseSchema);
 */

import { z } from 'zod';

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export const UserSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  full_name: z.string(),
  organization_id: z.number(),
  organization_name: z.string().optional(),
  is_demo: z.boolean(),
  is_active: z.boolean(),
  is_superuser: z.boolean(),
  roles: z.array(z.string()).optional(),
  permissions: z.array(z.string()).optional(),
});

export const LoginResponseSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
  user: UserSchema.optional(),
});

export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type User = z.infer<typeof UserSchema>;

// ---------------------------------------------------------------------------
// Workspace preferences
// ---------------------------------------------------------------------------

export const WorkspacePreferencesResponseSchema = z.object({
  status: z.string(),
  data: z.object({
    default_workspace: z.string().nullable().optional(),
    recent_workspaces: z.array(z.string()).optional(),
    show_gateway_on_login: z.boolean().optional(),
    last_workspace: z.string().nullable().optional(),
  }).optional(),
});

export type WorkspacePreferencesResponse = z.infer<typeof WorkspacePreferencesResponseSchema>;

// ---------------------------------------------------------------------------
// BrAPI pagination envelope (used by most list endpoints)
// ---------------------------------------------------------------------------

export const BrAPIPaginationSchema = z.object({
  currentPage: z.number(),
  pageSize: z.number(),
  totalCount: z.number(),
  totalPages: z.number(),
});

export const BrAPIMetadataSchema = z.object({
  datafiles: z.array(z.unknown()).optional(),
  pagination: BrAPIPaginationSchema,
  status: z.array(z.object({
    message: z.string(),
    messageType: z.string(),
  })).optional(),
});

/**
 * Generic BrAPI list response schema factory.
 * Usage: BrAPIListResponseSchema(GermplasmSchema)
 */
export function BrAPIListResponseSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    metadata: BrAPIMetadataSchema,
    result: z.object({
      data: z.array(itemSchema),
    }),
  });
}

/**
 * Generic BrAPI single-item response schema factory.
 * Usage: BrAPISingleResponseSchema(ProgramSchema)
 */
export function BrAPISingleResponseSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    metadata: BrAPIMetadataSchema,
    result: itemSchema,
  });
}

// ---------------------------------------------------------------------------
// Health / status endpoints
// ---------------------------------------------------------------------------

export const HealthResponseSchema = z.object({
  status: z.string(),
  assistant: z.string().optional(),
  active_provider: z.string().optional(),
});

// ---------------------------------------------------------------------------
// Chat / REEVU
// ---------------------------------------------------------------------------

export const ChatResponseSchema = z.object({
  request_id: z.string(),
  message: z.string(),
  provider: z.string(),
  model: z.string(),
  model_confirmed: z.boolean().optional(),
  context: z.array(z.unknown()).nullable().optional(),
  conversation_id: z.string().nullable().optional(),
  suggestions: z.array(z.string()).nullable().optional(),
  cached: z.boolean().optional(),
  latency_ms: z.number().nullable().optional(),
  function_call: z.record(z.unknown()).nullable().optional(),
  function_result: z.record(z.unknown()).nullable().optional(),
  policy_validation: z.record(z.unknown()).nullable().optional(),
  evidence_envelope: z.record(z.unknown()).nullable().optional(),
  retrieval_audit: z.record(z.unknown()).nullable().optional(),
  plan_execution_summary: z.record(z.unknown()).nullable().optional(),
  comparison_result: z.record(z.unknown()).nullable().optional(),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;
