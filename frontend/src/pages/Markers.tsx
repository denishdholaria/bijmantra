
import React from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, Marker } from "@/api/genotyping";
import { Badge } from "@/components/ui/badge";

export const Markers = () => {
  return (
    <BrAPIListPage<Marker>
      title="Genomic Markers"
      description="List of all genetic markers available in the system."
      entityName="Marker"
      queryKey={["markers"]}
      queryFn={GenotypingService.getMarkers}
      searchPlaceholder="Search by marker name..."
      columns={[
        {
          header: "Marker Name",
          accessorKey: "markerName",
          cell: (item) => <div className="font-medium">{item.markerName || item.defaultDisplayName}</div>,
        },
        {
          header: "Type",
          accessorKey: "markerType",
          cell: (item) => <Badge variant="outline">{item.markerType}</Badge>,
        },
        {
          header: "Ref/Alt",
          cell: (item) => (
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
          cell: (item) => (
            <div className="text-sm text-muted-foreground">
              {item.synonyms?.join(", ") || "-"}
            </div>
          ),
        },
        {
          header: "Analysis Methods",
          cell: (item) => item.analysisMethods?.join(", ") || "-",
        },
      ]}
    />
  );
};

export default Markers;
