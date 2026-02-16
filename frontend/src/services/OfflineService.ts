import { apiClient } from '@/lib/api-client';
import { db } from '@/lib/db';

export class OfflineService {
  /**
   * Download a full study (metadata, layout, traits) for offline use.
   * This populates the Dexie local database.
   */
  async downloadStudy(studyId: string) {
    console.log(`📥 Downloading study ${studyId}...`);

    try {
      // 1. Fetch Study Details (for Trials Metadata)
      // We assume /studies list gives enough info, or we fetch individually if needed.
      // For now, we'll hit the entries endpoint which returns study info too.
      
      // 2. Fetch Entries (Plots)
      const entriesRes = await apiClient.get<any>(`/api/v2/field-book/studies/${studyId}/entries`);
      const { entries, study_name } = entriesRes;

      // 3. Fetch Traits
      const traitsRes = await apiClient.get<any>(`/api/v2/field-book/studies/${studyId}/traits`);
      const { traits } = traitsRes;

      // 4. Save to Local DB Transactionally
      await db.transaction('rw', db.trials, db.plots, async () => {
        // Save Trial/Study Info
        await db.trials.put({
          id: studyId,
          name: study_name || studyId,
          programName: 'Unknown', // API might need to return this
          active: true,
          lastSync: Date.now()
        });

        // Save Plots
        const plotsToSave = entries.map((e: any) => ({
          id: e.plot_id, // Using plot_id as key
          trialId: studyId,
          accessionId: e.germplasm, // Using name as ID for now if DB ID missing
          accessionName: e.germplasm,
          replicate: e.rep,
          block: e.block,
          plotNumber: parseInt(e.plot_id.split('-').pop() || '0') // simplistic parsing
        }));
        await db.plots.bulkPut(plotsToSave);

        // Save Traits
        const traitsToSave = traits.map((t: any) => ({
          id: t.id, // trait code
          trialId: studyId,
          name: t.name,
          dataType: t.data_type,
          min: t.min,
          max: t.max,
          unit: t.unit
        }));
        await db.traits.bulkPut(traitsToSave);
        
        console.log(`✅ Downloaded ${entries.length} plots and ${traits.length} traits for ${studyId}`);
      });

      return { success: true, count: entries.length };
    } catch (error) {
      console.error('❌ Failed to download study:', error);
      throw error;
    }
  }

  /**
   * Get list of downloadable studies from backend
   */
  async getAvailableStudies() {
    const res = await apiClient.get<any>('/api/v2/field-book/studies');
    return res.studies || [];
  }
}

export const offlineService = new OfflineService();
