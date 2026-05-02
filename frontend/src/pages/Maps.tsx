
import React, { useMemo } from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, GenomicMap } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const Maps = () => {
  const columns = useMemo(() => [
    {
      header: "Map Name",
      accessorKey: "mapName" as keyof GenomicMap,
      cell: (item: GenomicMap) => <div className="font-medium">{item.mapName}</div>,
    },
    {
      header: "Type",
      accessorKey: "type" as keyof GenomicMap,
      cell: (item: GenomicMap) => <Badge variant="outline">{item.type}</Badge>,
    },
    {
      header: "Stats",
      cell: (item: GenomicMap) => (
        <div className="flex gap-2 text-sm">
           <span>{item.linkageGroupCount} LGs</span>
           <span className="text-muted-foreground">•</span>
           <span>{item.markerCount?.toLocaleString()} Markers</span>
        </div>
      ),
    },
    {
      header: "Published",
      accessorKey: "publishedDate" as keyof GenomicMap,
      cell: (item: GenomicMap) => item.publishedDate ? new Date(item.publishedDate).toLocaleDateString() : "-",
    },
  ], []);

  return (
    <BrAPIListPage<GenomicMap>
      title="Genomic Maps"
      description="Linkage groups and marker positions."
      entityName="Map"
      queryKey={["maps"]}
      queryFn={GenotypingService.getMaps}
      searchPlaceholder="Search maps..."
      columns={columns}
    />
  );
};

export default Maps;
