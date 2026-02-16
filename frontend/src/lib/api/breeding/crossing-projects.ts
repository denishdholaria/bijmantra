import { ApiClientCore } from "../core/client";

export interface CrossingProject {
  crossingProjectDbId: string;
  crossingProjectName: string;
  crossingProjectDescription?: string;
  programDbId?: string;
  programName?: string;
  commonCropName?: string;
  plannedCrossCount?: number;
  completedCrossCount?: number;
  status?: string;
  startDate?: string;
  endDate?: string;
}

export class CrossingProjectsService {
  constructor(private client: ApiClientCore) {}

  async getProjects(params?: {
    commonCropName?: string;
    programDbId?: string;
    pageSize?: number;
    page?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.commonCropName)
      searchParams.set("commonCropName", params.commonCropName);
    if (params?.programDbId)
      searchParams.set("programDbId", params.programDbId);
    if (params?.pageSize)
      searchParams.set("pageSize", params.pageSize.toString());
    if (params?.page) searchParams.set("page", params.page.toString());
    const query = searchParams.toString();
    return this.client.get<{ result: { data: CrossingProject[] } }>(
      `/brapi/v2/crossingprojects${query ? `?${query}` : ""}`
    );
  }

  async getProject(crossingProjectDbId: string) {
    return this.client.get<{ result: CrossingProject }>(
      `/brapi/v2/crossingprojects/${crossingProjectDbId}`
    );
  }

  async createProject(data: Partial<CrossingProject>) {
    return this.client.post<{ result: { data: CrossingProject[] } }>(
      "/brapi/v2/crossingprojects",
      [data]
    );
  }

  async updateProject(
    crossingProjectDbId: string,
    data: Partial<CrossingProject>
  ) {
    return this.client.put<{ result: CrossingProject }>(
      `/brapi/v2/crossingprojects/${crossingProjectDbId}`,
      data
    );
  }

  async deleteProject(crossingProjectDbId: string) {
    return this.client.delete<void>(
      `/brapi/v2/crossingprojects/${crossingProjectDbId}`
    );
  }
}
