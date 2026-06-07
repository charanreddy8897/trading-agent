import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { portfolioApi, alertsApi } from '@/api/client'
import toast from 'react-hot-toast'

export function usePortfolioSummary() {
  return useQuery({ queryKey: ['portfolio', 'summary'], queryFn: portfolioApi.summary, refetchInterval: 60_000 })
}

export function useHoldings() {
  return useQuery({ queryKey: ['portfolio', 'holdings'], queryFn: portfolioApi.holdings, refetchInterval: 60_000 })
}

export function useSectorAllocation() {
  return useQuery({ queryKey: ['portfolio', 'sector-alloc'], queryFn: portfolioApi.sectorAlloc })
}

export function useAlerts() {
  const qc = useQueryClient()
  const query = useQuery({ queryKey: ['alerts'], queryFn: alertsApi.active, refetchInterval: 30_000 })
  const dismiss = useMutation({
    mutationFn: (id: number) => alertsApi.dismiss(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      toast.success('Alert dismissed')
    },
  })
  return { ...query, dismiss: dismiss.mutate }
}
