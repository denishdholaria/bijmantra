
import React from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, MarkerProfile } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const MarkerProfiles = () => {
  return (
    <BrAPIListPage<MarkerProfile>
      title="Marker Profiles"
      description="Genotype profiles for germplasm."
      entityName="Marker Profile"
      queryKey={["markerProfiles"]}
      queryFn={GenotypingService.getMarkerProfiles}
      searchPlaceholder="Search profiles..."
      columns={[
        {
          header: "Profile ID",
          accessorKey: "uniqueDisplayName",
          cell: (item) => <div className="font-medium">{item.uniqueDisplayName}</div>,
        },
        {
          header: "Germplasm ID",
          accessorKey: "germplasmDbId",
        },
        {
          header: "Extract ID",
          accessorKey: "extractDbId",
        },
        {
          header: "Analysis Method",
          accessorKey: "analysisMethod",
          cell: (item) => <Badge variant="outline">{item.analysisMethod}</Badge>,
        },
        {
          header: "Result Count",
          accessorKey: "resultCount",
          cell: (item) => item.resultCount?.toLocaleString(),
        },
      ]}
    />
  );
};

export default MarkerProfiles;
