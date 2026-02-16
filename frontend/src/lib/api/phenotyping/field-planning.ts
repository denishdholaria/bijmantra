import { ApiClientCore } from "../core/client";

export class FieldPlanningService {
  constructor(private client: ApiClientCore) {}

  // ===========================================
  // Field Plans
  // ===========================================

  async getFieldPlans(params?: {
    field_id?: string;
    season?: string;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.field_id) searchParams.append("field_id", params.field_id);
    if (params?.season) searchParams.append("season", params.season);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any>(`/api/v2/field-planning/plans?${searchParams}`);
  }

  async getFieldPlan(planId: string) {
    return this.client.get<any>(`/api/v2/field-planning/plans/${planId}`);
  }

  async getSeasonPlans(params?: {
    year?: number;
    season_type?: string;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.year) searchParams.append("year", params.year.toString());
    if (params?.season_type)
      searchParams.append("season_type", params.season_type);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any>(`/api/v2/field-planning/seasons?${searchParams}`);
  }

  async getSeasonPlan(planId: string) {
    return this.client.get<any>(`/api/v2/field-planning/seasons/${planId}`);
  }

  async getFieldPlanResources(planId: string) {
    return this.client.get<any>(`/api/v2/field-planning/resources/${planId}`);
  }

  async getFieldPlanningCalendar(year: number, month?: number) {
    const searchParams = new URLSearchParams();
    searchParams.append("year", year.toString());
    if (month) searchParams.append("month", month.toString());
    return this.client.get<any>(
      `/api/v2/field-planning/calendar?${searchParams}`
    );
  }

  async getFieldPlanningStatistics() {
    return this.client.get<any>("/api/v2/field-planning/statistics");
  }

  // ===========================================
  // Resource Management
  // ===========================================

  async getResourceOverview() {
    return this.client.get<any>("/api/v2/resources/overview");
  }

  // Budget
  async getBudgetCategories(year: number = 2025) {
    return this.client.get<any[]>(`/api/v2/resources/budget?year=${year}`);
  }

  async getBudgetSummary(year: number = 2025) {
    return this.client.get<any>(`/api/v2/resources/budget/summary?year=${year}`);
  }

  async updateBudgetCategory(categoryId: string, used: number) {
    return this.client.patch<any>(`/api/v2/resources/budget/${categoryId}`, {
      used,
    });
  }

  // Staff
  async getStaffAllocations() {
    return this.client.get<any[]>("/api/v2/resources/staff");
  }

  async getStaffSummary() {
    return this.client.get<any>("/api/v2/resources/staff/summary");
  }

  // Fields
  async getFieldAllocations() {
    return this.client.get<any[]>("/api/v2/resources/fields");
  }

  async getFieldAllocationSummary() {
    return this.client.get<any>("/api/v2/resources/fields/summary");
  }

  // Calendar
  async getCalendarEvents(params?: {
    start_date?: string;
    end_date?: string;
    event_type?: string;
    status?: string;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.start_date)
      searchParams.append("start_date", params.start_date);
    if (params?.end_date) searchParams.append("end_date", params.end_date);
    if (params?.event_type)
      searchParams.append("event_type", params.event_type);
    if (params?.status) searchParams.append("status", params.status);
    return this.client.get<any[]>(`/api/v2/resources/calendar?${searchParams}`);
  }

  async getCalendarEventsByDate(date: string) {
    return this.client.get<any[]>(`/api/v2/resources/calendar/date/${date}`);
  }

  async getCalendarSummary() {
    return this.client.get<any>("/api/v2/resources/calendar/summary");
  }

  async createCalendarEvent(event: {
    title: string;
    type?: string;
    date: string;
    time?: string;
    duration?: string;
    location?: string;
    assignee?: string;
    description?: string;
  }) {
    return this.client.post<any>("/api/v2/resources/calendar", event);
  }
}
