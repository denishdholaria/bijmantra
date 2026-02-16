export type MockProgram = {
  programDbId: string;
  programName: string;
};

export function createMockProgram(overrides: Partial<MockProgram> = {}): MockProgram {
  return {
    programDbId: 'P-1',
    programName: 'Demo Program',
    ...overrides,
  };
}
