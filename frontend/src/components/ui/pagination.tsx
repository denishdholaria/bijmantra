import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import React from 'react';

// Export sub-components to satisfy imports like PaginationContent, etc.
// These are mocks to satisfy the import requirements of BrAPIListPage.tsx

export const PaginationContent = ({ children }: { children: React.ReactNode }) => (
  <div className="flex flex-row items-center gap-1">{children}</div>
);

export const PaginationItem = ({ children }: { children: React.ReactNode }) => (
  <div className="flex items-center">{children}</div>
);

export const PaginationLink = ({
  isActive,
  onClick,
  children
}: {
  isActive?: boolean;
  onClick?: () => void;
  children: React.ReactNode
}) => (
  <Button
    variant={isActive ? "default" : "outline"}
    size="icon"
    className="h-8 w-8"
    onClick={onClick}
  >
    {children}
  </Button>
);

export const PaginationNext = ({ onClick }: { onClick?: () => void }) => (
  <Button variant="outline" size="icon" className="h-8 w-8" onClick={onClick}>
    <ChevronRight className="h-4 w-4" />
  </Button>
);

export const PaginationPrevious = ({ onClick }: { onClick?: () => void }) => (
  <Button variant="outline" size="icon" className="h-8 w-8" onClick={onClick}>
    <ChevronLeft className="h-4 w-4" />
  </Button>
);

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  pageSize?: number;
  totalCount?: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
}

export function Pagination({
  currentPage,
  totalPages,
  pageSize,
  totalCount,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [10, 20, 50, 100],
}: PaginationProps) {
  // If no pages, don't render anything
  if (totalPages <= 1 && (!totalCount || totalCount <= 0)) return null;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-4">
      {/* Page Size Selector */}
      {pageSize && onPageSizeChange && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Rows per page:</span>
          <Select
            value={pageSize.toString()}
            onValueChange={(value) => onPageSizeChange(Number(value))}
          >
            <SelectTrigger className="h-8 w-[70px]">
              <SelectValue placeholder={pageSize.toString()} />
            </SelectTrigger>
            <SelectContent>
              {pageSizeOptions.map((size) => (
                <SelectItem key={size} value={size.toString()}>
                  {size}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Page Navigation */}
      <div className="flex items-center gap-2">
        <div className="text-sm text-muted-foreground mr-4">
          Page {currentPage + 1} of {Math.max(1, totalPages)}
          {totalCount !== undefined && ` (${totalCount} items)`}
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => onPageChange(0)}
            disabled={currentPage === 0}
            title="First Page"
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>

          <PaginationPrevious onClick={() => onPageChange(currentPage - 1)} />

          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages - 1}
            title="Next Page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => onPageChange(totalPages - 1)}
            disabled={currentPage >= totalPages - 1}
            title="Last Page"
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
