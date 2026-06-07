import { useQuery } from '@tanstack/react-query'
import { moversApi, pegApi, newsApi } from '@/api/client'

export function useMovers(count = 10) {
  return useQuery({ queryKey: ['movers', count], queryFn: () => moversApi.top(count), refetchInterval: 60_000 })
}

export function useUnusualVolume() {
  return useQuery({ queryKey: ['movers', 'unusual'], queryFn: () => moversApi.unusual(), refetchInterval: 60_000 })
}

export function usePegSetups() {
  return useQuery({ queryKey: ['peg', 'active'], queryFn: pegApi.active, staleTime: 120_000 })
}

export function usePegHistory() {
  return useQuery({ queryKey: ['peg', 'history'], queryFn: pegApi.history, staleTime: 300_000 })
}

export function useNewsFeed(sector = 'all') {
  return useQuery({ queryKey: ['news', sector], queryFn: () => newsApi.feed(sector), staleTime: 120_000 })
}
