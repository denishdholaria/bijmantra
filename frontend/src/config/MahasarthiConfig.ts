import {
  Globe, // Prakriti (Environment)
  Sprout, // Srijan (Creation)
  Package, // Sampada (Assets)
  BarChart3, // Drishti (Insights)
  LayoutDashboard,
  LucideIcon,
} from "lucide-react";

export type GatewayId = "prakriti" | "srijan" | "sampada" | "drishti";

export interface GatewayConfig {
  id: GatewayId;
  label: string;
  iconName: string; // Lucide icon name
  description: string;
  color: string;
  landingRoute: string; // Default route when clicking gateway
  workspaces: string[]; // List of workspace IDs belonging to this gateway
}

export const GATEWAYS: Record<GatewayId, GatewayConfig> = {
  prakriti: {
    id: "prakriti",
    label: "Prakriti",
    iconName: "Globe",
    description: "Environment & Earth Systems",
    color: "bg-emerald-500",
    landingRoute: "/earth-systems/map",
    workspaces: ["atmosphere", "hydrology", "lithosphere", "biosphere"],
  },
  srijan: {
    id: "srijan",
    label: "Srijan",
    iconName: "Sprout",
    description: "Creation & Breeding",
    color: "bg-amber-500",
    landingRoute: "/programs",
    workspaces: ["breeding", "genomics", "phenotyping"],
  },
  sampada: {
    id: "sampada",
    label: "Sampada",
    iconName: "Package",
    description: "Assets & Operations",
    color: "bg-blue-500",
    landingRoute: "/seed-bank/dashboard",
    workspaces: ["seed-bank", "seed-operations", "inventory"],
  },
  drishti: {
    id: "drishti",
    label: "Drishti",
    iconName: "BarChart3",
    description: "Insights & Analytics",
    color: "bg-purple-500",
    landingRoute: "/analytics",
    workspaces: ["analytics", "impact", "knowledge"],
  },
};

// Helper to find which gateway a route belongs to
export function getGatewayForRoute(pathname: string): GatewayId | null {
  if (pathname.startsWith("/prakriti") || pathname.includes("earth-systems"))
    return "prakriti";
  if (pathname.includes("breeding") || pathname.includes("genomics"))
    return "srijan";
  if (pathname.includes("seed-bank") || pathname.includes("seed-ops"))
    return "sampada";
  if (pathname.includes("analytics") || pathname.includes("impact"))
    return "drishti";
  return null;
}
