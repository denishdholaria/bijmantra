
import React from "react";
import { BrAPIListPage } from "@/components/common/BrAPIListPage";
import { GenotypingService, ReferenceSet } from "@/api/genotyping";

export const ReferenceSets = () => {
  return (
    <BrAPIListPage<ReferenceSet>
      title="Reference Sets"
      description="Collections of reference sequences (genomes)."
      entityName="Reference Set"
      queryKey={["referenceSets"]}
      queryFn={GenotypingService.getReferenceSets}
      searchPlaceholder="Search reference sets..."
      columns={[
        {
          header: "Set Name",
          accessorKey: "referenceSetName",
          cell: (item) => (
             <div>
              <div className="font-medium">{item.referenceSetName}</div>
              <div className="text-xs text-muted-foreground">{item.description}</div>
            </div>
          ),
        },
        {
          header: "Species",
          cell: (item) => item.species?.commonName || "-",
        },
        {
          header: "Assembly PUI",
          accessorKey: "assemblyPUI",
          cell: (item) => <div className="font-mono text-sm">{item.assemblyPUI}</div>,
        },
         {
          header: "Source",
          cell: (item) => item.sourceUri ? (
             <a href={item.sourceUri} target="_blank" rel="noreferrer" className="text-sm text-primary hover:underline">
               Link
             </a>
          ) : "-",
        },
      ]}
    />
  );
};

export default ReferenceSets;
