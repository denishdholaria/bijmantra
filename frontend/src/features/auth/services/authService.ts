/**
 * Auth Service
 * 
 * Handles authentication API calls and navigation logic.
 */

import { getWorkspace } from '@/framework/registry/workspaces';
import type { WorkspaceId } from '@/types/workspace';
import type { LoginFormData, LoginResult } from '../types';

export class AuthService {
  /**
   * Determines navigation target after successful login
   */
  static determinePostLoginNavigation(
    defaultWorkspace: string | null,
    showGatewayOnLogin: boolean
  ): LoginResult {
    // If user has a default workspace and doesn't want to see gateway, go directly there
    if (defaultWorkspace && !showGatewayOnLogin) {
      const workspace = getWorkspace(defaultWorkspace as WorkspaceId);
      if (workspace) {
        return {
          success: true,
          shouldNavigateToGateway: false,
          workspaceRoute: workspace.landingRoute,
        };
      }
    }

    // Otherwise, show the workspace gateway
    return {
      success: true,
      shouldNavigateToGateway: true,
    };
  }
}
