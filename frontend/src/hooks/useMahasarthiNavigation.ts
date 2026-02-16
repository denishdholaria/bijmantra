
import { useState, useEffect, useMemo, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDockStore } from '@/store/dockStore';
import { useDivisionRegistry } from '@/framework/registry';
import { useActiveWorkspace, useWorkspaceStore } from '@/store/workspaceStore';
import { getWorkspaceModules } from '@/framework/registry/workspaces';
import { GATEWAYS, GatewayId, getGatewayForRoute } from '@/config/MahasarthiConfig';

export function useMahasarthiNavigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const { pinnedItems, recentItems } = useDockStore();
  const { navigableDivisions } = useDivisionRegistry();
  const activeWorkspace = useActiveWorkspace();
  const activeWorkspaceId = useWorkspaceStore((state) => state.activeWorkspaceId);

  // Gateway State
  const [activeGateway, setActiveGateway] = useState<GatewayId>('srijan');

  // Sync active gateway with route
  useEffect(() => {
    const gateway = getGatewayForRoute(location.pathname);
    if (gateway) {
      setActiveGateway(gateway);
    }
  }, [location.pathname]);

  const handleGatewaySelect = useCallback((id: GatewayId) => {
    setActiveGateway(id);
    navigate(GATEWAYS[id].landingRoute);
  }, [navigate]);

  // Filter divisions by Active Gateway Workspaces
  const filteredDivisions = useMemo(() => {
    // Logic: A division belongs to the gateway if its route matches one of the gateway's workspaces
    // or through explicit mapping if available.
    // Fallback logic from original component:
    return navigableDivisions.filter(division => {
      const divisionId = division.id;
      
      if (activeGateway === 'srijan' && (divisionId === 'breeding' || divisionId === 'genomics' || divisionId === 'plant-sciences')) return true;
      if (activeGateway === 'sampada' && (divisionId === 'seed-bank' || divisionId === 'seed-operations' || divisionId === 'commercial')) return true;
      if (activeGateway === 'prakriti' && (divisionId === 'earth-systems' || divisionId === 'sun-earth-systems' || divisionId === 'space-research')) return true;
      if (activeGateway === 'drishti' && (divisionId === 'sensor-networks' || divisionId === 'knowledge' || divisionId === 'integrations')) return true;
      
      return false;
    });
  }, [navigableDivisions, activeGateway]);

  // Filter pinned items by Gateway Context
  // For Sidebar: Limit to top 5 to avoid clutter
  // For Dock: We might want all of them, but this hook returns the context-aware list
  const gatewayPinnedItems = useMemo(() => {
     return pinnedItems
       .filter(item => getGatewayForRoute(item.path) === activeGateway);
  }, [pinnedItems, activeGateway]);

  // Filter recent items by Gateway Context
  const gatewayRecentItems = useMemo(() => {
    return recentItems
      .filter(item => getGatewayForRoute(item.path) === activeGateway)
      .slice(0, 4); // Keep recent items concise
 }, [recentItems, activeGateway]);

  // Active Workspace Modules
  const workspaceModules = useMemo(() => {
    return activeWorkspace ? getWorkspaceModules(activeWorkspace.id) : [];
  }, [activeWorkspace]);

  return {
    activeGateway,
    activeWorkspace,
    activeWorkspaceId,
    filteredDivisions,
    gatewayPinnedItems,
    gatewayRecentItems,
    workspaceModules,
    handleGatewaySelect,
    GATEWAYS
  };
}
