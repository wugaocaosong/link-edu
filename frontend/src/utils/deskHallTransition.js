import { nextTick } from 'vue'

export async function travelBetweenDeskAndHall(event, router, destination) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  const root = document.documentElement
  if (root.dataset.deskTravel) return
  if (!document.startViewTransition || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return router.push(destination)
  }
  root.dataset.deskTravel = destination === '/courses' ? 'up' : 'down'
  try {
    const transition = document.startViewTransition(async () => {
      await router.push(destination)
      await nextTick()
    })
    await transition.finished
  } finally {
    delete root.dataset.deskTravel
  }
}
