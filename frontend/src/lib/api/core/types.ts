
export interface BrAPIMetadata {
  datafiles: string[];
  pagination: {
    currentPage: number;
    pageSize: number;
    totalCount: number;
    totalPages: number;
  };
  status: Array<{
    message: string;
    messageType: string;
  }>;
}

export interface BrAPIResponse<T> {
  metadata: BrAPIMetadata;
  result: T;
}

export interface BrAPIListResponse<T> {
  metadata: BrAPIMetadata;
  result: {
    data: T[];
  };
}
