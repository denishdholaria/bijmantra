import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export class ImagesService {
  constructor(private client: ApiClientCore) {}

  async getImages(page = 0, pageSize = 100) {
    return this.client.get<BrAPIListResponse<any>>(
      `/brapi/v2/images?page=${page}&pageSize=${pageSize}`
    );
  }

  async createImage(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/images", data);
  }

  async uploadImageFile(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    return this.client.post<BrAPIResponse<{ imageURL: string }>>(
      "/brapi/v2/images/upload",
      formData
    );
  }
}
