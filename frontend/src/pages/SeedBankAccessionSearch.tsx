import { useSearchParams } from 'react-router-dom';
import { AccessionDetailView, AccessionSearchPage } from '@/divisions/seed-bank/accession-search';

export function SeedBankAccessionSearch() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedAccessionId = searchParams.get('accession');

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
      <AccessionSearchPage
        selectedAccessionId={selectedAccessionId}
        onSelectAccession={(accessionId) => {
          const nextParams = new URLSearchParams(searchParams);
          nextParams.set('accession', accessionId);
          setSearchParams(nextParams);
        }}
      />
      <AccessionDetailView accessionId={selectedAccessionId} />
    </div>
  );
}

export default SeedBankAccessionSearch;
