
import React, { useMemo } from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, Marker } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const Markers = () => {
  const columns = useMemo(() => [
    {
      header: "Marker Name",
      accessorKey: "markerName" as keyof Marker,
      cell: (item: Marker) => <div className="font-medium">{item.markerName || item.defaultDisplayName}</div>,
    },
    {
      header: "Type",
      accessorKey: "markerType" as keyof Marker,
      cell: (item: Marker) => <Badge variant="outline">{item.markerType}</Badge>,
    },
    {
      header: "Ref/Alt",
      cell: (item: Marker) => (
        <div className="flex gap-1">
          {item.refAlt?.map((base, i) => (
            <Badge key={i} variant="secondary" className="font-mono text-xs">
              {base}
            </Badge>
          ))}
        </div>
      ),
    },
    {
      header: "Synonyms",
      cell: (item: Marker) => (
        <div className="text-sm text-muted-foreground">
          {item.synonyms?.join(", ") || "-"}
        </div>
      ),
    },
    {
      header: "Analysis Methods",
      cell: (item: Marker) => item.analysisMethods?.join(", ") || "-",
    },
  ], []);

  return (
    <BrAPIListPage<Marker>
      title="Genomic Markers"
      description="List of all genetic markers available in the system."
      entityName="Marker"
      queryKey={["markers"]}
      queryFn={GenotypingService.getMarkers}
      searchPlaceholder="Search by marker name..."
      columns={columns}
    />
  );
};

export default Markers;
