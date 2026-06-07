import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { analysisApi } from '@/api/client'
import toast from 'react-hot-toast'

export function useAnalysis(ticker: string) {
  return useQuery({
    queryKey: ['analysis', ticker],
    queryFn:  () => analysisApi.get(ticker),
    enabled:  !!ticker,
    staleTime: 300_000,
  })
}

export function useRefreshAnalysis(ticker: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => analysisApi.refresh(ticker),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analysis', ticker] })
      toast.success(`${ticker} analysis refreshed`)
    },
    onError: (e: Error) => toast.error(e.message),
  })
}
