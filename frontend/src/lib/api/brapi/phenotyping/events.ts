import { ApiClientCore } from "../../core/client";
import { BrAPIListResponse, BrAPIResponse } from "../../core/types";

export class EventsService {
  constructor(private client: ApiClientCore) {}

  async getEvents(studyDbId?: string, page = 0, pageSize = 100) {
    const params = new URLSearchParams({
      page: String(page),
      pageSize: String(pageSize),
    });
    if (studyDbId) params.append("studyDbId", studyDbId);
    return this.client.get<BrAPIListResponse<any>>(`/brapi/v2/events?${params}`);
  }

  async getEvent(eventDbId: string) {
    return this.client.get<BrAPIResponse<any>>(`/brapi/v2/events/${eventDbId}`);
  }

  async createEvent(data: any) {
    return this.client.post<BrAPIResponse<any>>("/brapi/v2/events", data);
  }

  async deleteEvent(eventDbId: string) {
    return this.client.delete<any>(`/brapi/v2/events/${eventDbId}`);
  }
}
