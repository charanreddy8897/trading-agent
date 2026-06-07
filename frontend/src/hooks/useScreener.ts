import { useQuery } from '@tanstack/react-query'
import { screenerApi } from '@/api/client'

export function useScreener(sector = 'all', minScore = 0) {
  return useQuery({
    queryKey: ['screener', sector, minScore],
    queryFn:  () => screenerApi.ranked(sector, minScore),
    staleTime: 60_000,
  })
}
