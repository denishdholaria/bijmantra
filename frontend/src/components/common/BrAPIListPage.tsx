
import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Search, RefreshCw, FileText } from "lucide-react";
import { BrAPIResponse } from "@/api/genotyping";

interface ColumnDef<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => React.ReactNode;
}

interface BrAPIListPageProps<T> {
  title: string;
  description?: string;
  queryKey: string[];
  queryFn: (params: { page: number; pageSize: number; [key: string]: any }) => Promise<BrAPIResponse<T>>;
  columns: ColumnDef<T>[];
  searchPlaceholder?: string;
  onSearch?: (term: string) => void;
  entityName?: string;
}

export function BrAPIListPage<T>({
  title,
  description,
  queryKey,
  queryFn,
  columns,
  searchPlaceholder = "Search...",
  entityName = "Items",
}: BrAPIListPageProps<T>) {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  
  // Debounce search could be added here, for now direct pass
  const queryParams = {
    page,
    pageSize,
    ...(searchTerm ? { name: searchTerm } : {}), // Generic search param, usually needs specific key like 'markerName'
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [...queryKey, page, pageSize, searchTerm],
    queryFn: () => queryFn(queryParams),
    placeholderData: (previousData) => previousData,
  });

  const metadata = data?.metadata?.pagination;
  const items = data?.result?.data || [];
  const totalPages = metadata?.totalPages || 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        {description && <p className="text-muted-foreground">{description}</p>}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="text-lg font-medium">
            {entityName} List
          </CardTitle>
          <div className="flex items-center gap-2">
             <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                className="pl-8 w-[250px]"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline" size="icon" onClick={() => refetch()}>
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((col, idx) => (
                    <TableHead key={idx}>{col.header}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading data...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : isError ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center text-red-500">
                      Error loading data. Please try again.
                    </TableCell>
                  </TableRow>
                ) : items.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={columns.length} className="h-24 text-center">
                      No results found.
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item, rowIdx) => (
                    <TableRow key={rowIdx}>
                      {columns.map((col, colIdx) => (
                        <TableCell key={colIdx}>
                          {col.cell
                            ? col.cell(item)
                            : col.accessorKey
                            ? String(item[col.accessorKey] ?? "")
                            : "-"}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
             <div className="flex items-center justify-end space-x-2 py-4">
              <div className="flex-1 text-sm text-muted-foreground">
                Page {page + 1} of {totalPages}
              </div>
              <div className="space-x-2 flex">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0 || isLoading}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1 || isLoading}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
