/** 板块封面：与 doc-*.svg 同款的文字版式封面（由 scripts/generate_board_covers.cjs 生成）。 */
export const libraryBoardCovers = {
  'ntce-primary': '/library/covers/board-ntce-primary.svg',
  'ntce-secondary': '/library/covers/board-ntce-secondary.svg',
  'ntce-kindergarten': '/library/covers/board-ntce-kindergarten.svg',
  'fraction-knowledge': '/library/covers/board-fraction-knowledge.svg',
  'fraction-misconceptions': '/library/covers/board-fraction-misconceptions.svg',
  'fraction-micro-lesson': '/library/covers/board-fraction-micro-lesson.svg',
  'presentation-checklist': '/library/covers/board-presentation-checklist.svg',
  'review-six-dimensions': '/library/covers/board-review-six-dimensions.svg',
  'review-evidence-threshold': '/library/covers/board-review-evidence-threshold.svg',
  'puer-case': '/library/covers/board-puer-case.svg',
  'tangshan-assessment': '/library/covers/board-tangshan-assessment.svg',
  'external-links': '/library/covers/board-external-links.svg',
};

/**
 * 兜底封面：视频条目走 thumbnail、图示条目走 boardImage、文稿条目走
 * covers/doc-*.svg，都没有时用这张，避免分类网格出现空白破图。
 */
const FALLBACK_COVER = '/library/covers/board-fraction-knowledge.svg';

export function boardCoverFor(item) {
  if (!item) return '';
  return item.boardImage || libraryBoardCovers[item.id] || item.thumbnail || FALLBACK_COVER;
}
