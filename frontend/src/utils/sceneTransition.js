import { nextTick } from 'vue'

export async function travelScene(event, router, destination, direction) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  const root = document.documentElement
  if (root.dataset.deskTravel) return
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return router.push(destination)
  }
  root.dataset.deskTravel = direction
  try {
    if (!document.startViewTransition) {
      await router.push(destination)
      await nextTick()
      const slots = document.querySelectorAll('.page-frame > .page-slot')
      await Promise.allSettled([...slots].flatMap(slot => slot.getAnimations().map(animation => animation.finished)))
      return
    }
    const transition = document.startViewTransition(async () => {
      await router.push(destination)
      await nextTick()
    })
    await transition.finished
  } finally {
    delete root.dataset.deskTravel
  }
}
