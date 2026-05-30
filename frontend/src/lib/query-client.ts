import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: false,
      refetchOnWindowFocus: false,
      // In the preview environment, many endpoints return 404 because the full
      // backend is not running. Normalise those errors so pages can detect them
      // and render PreviewUnavailable instead of a raw error message.
      throwOnError: false,
    },
  },
})
