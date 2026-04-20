// Since I don't want to create a separate types file unless necessary, I will define interfaces here and export them.
// The existing components have local interfaces. I will unify them here.

export interface VisionDataset {
  id: string;
  name: string;
  description: string;
  dataset_type: string;
  crop: string;
  classes: string[];
  status: string;
  image_count: number;
  annotated_count: number;
  quality_score: number;
  created_at?: string;
  updated_at?: string;
  train_split?: number;
  val_split?: number;
  test_split?: number;
}

export interface VisionModel {
  id: string;
  name: string;
  crop: string;
  accuracy: number;
  status: string;
  downloads: number;
  description?: string;
  author?: string;
  size_mb?: number;
  tags?: string[];
  published_at?: string;
  version?: string;
  likes?: number;
}

export interface VisionImage {
  id: string;
  filename: string;
  url: string;
  width?: number;
  height?: number;
  annotation?: {
    label?: string;
    boxes?: Array<{ x: number; y: number; width: number; height: number; label: string }>;
  };
  split?: string;
}

export interface TrainingJob {
  id: string;
  name: string;
  dataset_id: string;
  base_model: string;
  backend: string;
  status: string;
  hyperparameters: Record<string, unknown>;
  metrics: Record<string, number>;
  progress: number;
  current_epoch: number;
  total_epochs: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  model_id: string | null;
}

const API_BASE = '/api/v2/vision';
const BRAPI_BASE = '/brapi/v2';

export const VisionService = {
  // Datasets
  async getDatasets(): Promise<{ datasets: VisionDataset[] }> {
    const res = await fetch(`${API_BASE}/datasets`);
    if (!res.ok) throw new Error('Failed to fetch datasets');
    return res.json();
  },

  async getDataset(id: string): Promise<{ dataset: VisionDataset }> {
    const res = await fetch(`${API_BASE}/datasets/${id}`);
    if (!res.ok) throw new Error('Failed to fetch dataset');
    return res.json();
  },

  async createDataset(data: Partial<VisionDataset>): Promise<{ dataset: VisionDataset }> {
    const res = await fetch(`${API_BASE}/datasets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create dataset');
    return res.json();
  },

  async deleteDataset(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/datasets/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete dataset');
  },

  // Images & Upload
  async uploadImageFile(file: File): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);

    // Using BrAPI endpoint for file upload
    const res = await fetch(`${BRAPI_BASE}/images/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const error = await res.text();
      throw new Error(`Upload failed: ${error}`);
    }

    const data = await res.json();
    // BrAPI response structure: { result: { imageURL: "..." } }
    return data.result.imageURL;
  },

  async addImagesToDataset(datasetId: string, images: Partial<VisionImage>[]): Promise<any> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/images`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ images }),
    });
    if (!res.ok) throw new Error('Failed to add images to dataset');
    return res.json();
  },

  async getDatasetImages(datasetId: string, limit = 100, offset = 0): Promise<{ images: VisionImage[] }> {
    const res = await fetch(`${API_BASE}/datasets/${datasetId}/images?limit=${limit}&offset=${offset}`);
    if (!res.ok) throw new Error('Failed to fetch images');
    return res.json();
  },

  // Annotations
  async saveBoundingBox(datasetId: string, imageId: string, boxes: any[]): Promise<any> {
    const res = await fetch(`${API_BASE}/annotations/bounding-box?dataset_id=${datasetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_id: imageId, boxes }),
    });
    if (!res.ok) throw new Error('Failed to save annotation');
    return res.json();
  },

  async getImageAnnotations(imageId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/images/${imageId}/annotations`);
    if (!res.ok) throw new Error('Failed to fetch annotations');
    return res.json();
  },

  // Models & Training
  async getModels(): Promise<{ models: VisionModel[] }> {
    const res = await fetch(`${API_BASE}/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    return res.json();
  },

  async getTrainingJobs(): Promise<{ jobs: TrainingJob[] }> {
    const res = await fetch(`${API_BASE}/training/jobs`);
    if (!res.ok) throw new Error('Failed to fetch training jobs');
    return res.json();
  },

  async createTrainingJob(data: any): Promise<{ job: TrainingJob }> {
    const res = await fetch(`${API_BASE}/training/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create training job');
    return res.json();
  }
};
