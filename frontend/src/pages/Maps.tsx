
import React from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, GenomicMap } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const Maps = () => {
  return (
    <BrAPIListPage<GenomicMap>
      title="Genomic Maps"
      description="Linkage groups and marker positions."
      entityName="Map"
      queryKey={["maps"]}
      queryFn={GenotypingService.getMaps}
      searchPlaceholder="Search maps..."
      columns={[
        {
          header: "Map Name",
          accessorKey: "mapName",
          cell: (item) => <div className="font-medium">{item.mapName}</div>,
        },
        {
          header: "Type",
          accessorKey: "type",
          cell: (item) => <Badge variant="outline">{item.type}</Badge>,
        },
        {
          header: "Stats",
          cell: (item) => (
            <div className="flex gap-2 text-sm">
               <span>{item.linkageGroupCount} LGs</span>
               <span className="text-muted-foreground">•</span>
               <span>{item.markerCount?.toLocaleString()} Markers</span>
            </div>
          ),
        },
        {
          header: "Published",
          accessorKey: "publishedDate",
          cell: (item) => item.publishedDate ? new Date(item.publishedDate).toLocaleDateString() : "-",
        },
      ]}
    />
  );
};

export default Maps;
