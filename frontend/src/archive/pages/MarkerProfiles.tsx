
import React, { useMemo } from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, MarkerProfile } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const MarkerProfiles = () => {
  const columns = useMemo(() => [
    {
      header: "Profile ID",
      accessorKey: "uniqueDisplayName" as keyof MarkerProfile,
      cell: (item: MarkerProfile) => <div className="font-medium">{item.uniqueDisplayName}</div>,
    },
    {
      header: "Germplasm ID",
      accessorKey: "germplasmDbId" as keyof MarkerProfile,
    },
    {
      header: "Extract ID",
      accessorKey: "extractDbId" as keyof MarkerProfile,
    },
    {
      header: "Analysis Method",
      accessorKey: "analysisMethod" as keyof MarkerProfile,
      cell: (item: MarkerProfile) => <Badge variant="outline">{item.analysisMethod}</Badge>,
    },
    {
      header: "Result Count",
      accessorKey: "resultCount" as keyof MarkerProfile,
      cell: (item: MarkerProfile) => item.resultCount?.toLocaleString(),
    },
  ], []);

  return (
    <BrAPIListPage<MarkerProfile>
      title="Marker Profiles"
      description="Genotype profiles for germplasm."
      entityName="Marker Profile"
      queryKey={["markerProfiles"]}
      queryFn={GenotypingService.getMarkerProfiles}
      searchPlaceholder="Search profiles..."
      columns={columns}
    />
  );
};

export default MarkerProfiles;
