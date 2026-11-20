/**
 * 资源库分类口径（2026-11-19 下拉菜单版 · 三维度）
 *
 * 雅婷反馈：单下拉只有 4 类又太少，改成三个标签各配一个下拉菜单：
 *   主题（备课 / 试讲与答辩 / 课例观摩 / 备考与官方资料）
 *   模块（站内文稿 / 图示板书 / 视频 / 下载包 / 站外链接）
 *   体量（速览 / 精读 / 整套）
 * 主题按备赛动作分；模块按资料形态分；体量按「一次要看多久」分。
 * 三个维度可任意组合，各自都能单独选「全部」。
 */

export const SCENE_OPTIONS = ["备课", "试讲与答辩", "课例观摩", "备考与官方资料"];

export const MODULE_OPTIONS = ["站内文稿", "图示板书", "视频", "下载包", "站外链接"];

export const LENGTH_OPTIONS = ["速览", "精读", "整套"];

export const LENGTH_HINT = {
  速览: "10 分钟以内，图示、短视频、外链速查",
  精读: "10–30 分钟，正经坐下来读的稿子",
  整套: "成包下载，解压后慢慢用",
};

const SCENE_BY_ID = {
  备课: [
    "info-knowledge",
    "info-misconceptions",
    "info-micro-lesson",
    "info-prep-checklist",
    "info-board-layout",
    "pack-required1-lesson-plans",
    "pack-demo-lesson-handouts",
    "doc-lesson-plan",
    "doc-lesson-hook",
    "doc-question-design",
    "doc-objective-verbs",
    "diagram-board-zoning",
    "diagram-stance-sightline",
    "diagram-wait-time",
    "diagram-lesson-timeline",
    "vid-prepare-fast",
  ],
  试讲与答辩: [
    "doc-verbatim-info",
    "doc-verbatim-pinyin",
    "doc-no-student",
    "doc-failures-20",
    "doc-nerves",
    "pack-verbatim-info-all",
    "vid-core-methods",
    "vid-trial-lecture-skills",
    "doc-trial-defense",
    "doc-structured-phenomenon",
    "doc-structured-emergency",
    "doc-structured-relationship",
    "doc-structured-activity",
    "doc-structured-viewpoint",
    "doc-structured-self",
    "pack-structured-interview",
    "pack-structured-real-questions",
    "pack-structured-200q",
    "pack-interview-faq",
    "pack-universal-templates",
  ],
  课例观摩: [
    "puer-case",
    "tangshan-assessment",
    "yau-english-case",
    "cqnu-english-case",
    "huhst-chemistry-case",
    "vid-demo-math-junior",
    "vid-demo-infosec-senior",
    "vid-demo-data-senior",
    "vid-mock-interview-full",
    "vid-trial-lecture-sample",
  ],
  备考与官方资料: [
    "presentation-checklist",
    "doc-structured-week",
    "doc-exam-day",
    "doc-board-check",
    "doc-device-check",
    "doc-time-table",
    "doc-self-review",
    "vid-interview-process",
    "ntce-primary",
    "ntce-secondary",
    "ntce-kindergarten",
    "review-six-dimensions",
    "review-evidence-threshold",
    "review-comment-phrases",
    "review-valid-examples",
    "external-links",
    "link-smartedu",
    "link-jszg",
    "link-pep",
    "doc-sources-index",
  ],
};

/** 旧分类字段兜底：新条目没进上面的表时按旧分类猜 */
const SCENE_BY_CATEGORY = {
  官方标准: "备考与官方资料",
  课题专包: "备课",
  图示素材: "备课",
  评课说明: "备考与官方资料",
  外部资源: "备考与官方资料",
  院校案例: "课例观摩",
  案例视频: "课例观摩",
  实操清单: "备考与官方资料",
  技巧视频: "试讲与答辩",
  训练文稿: "试讲与答辩",
};

const ID_TO_SCENE = Object.entries(SCENE_BY_ID).reduce((acc, [scene, ids]) => {
  ids.forEach((id) => { acc[id] = scene; });
  return acc;
}, {});

export function sceneOf(item) {
  return ID_TO_SCENE[item.id] || SCENE_BY_CATEGORY[item.category] || "备考与官方资料";
}

/** 模块：这份资料长什么样、从哪儿看 */
export function moduleOf(item) {
  const readUrl = item.readUrl || "";
  if (/^https?:/i.test(readUrl)) return "站外链接";
  const fmt = String(item.format || "");
  if (fmt.startsWith("文件包")) return "下载包";
  if (item.id.startsWith("vid-") || fmt.includes("MP4") || fmt.includes("视频")) return "视频";
  if (item.id.startsWith("diagram-") || fmt.includes("SVG") || fmt.includes("图示")) return "图示板书";
  const download = item.downloadName || item.downloadUrl || "";
  if (/\.(zip|docx?|pdf)$/i.test(download)) return "下载包";
  return "站内文稿";
}

/** 视频时长「7′43″ / 38′10″」转分钟 */
function durationMinutes(duration) {
  const match = /(\d+)′(?:(\d+)″)?/.exec(String(duration || ""));
  if (!match) return null;
  return Number(match[1]) + (Number(match[2] || 0) / 60);
}

/** 体量：一次要看多久（10 分钟内速览 / 10–30 分钟精读 / 成套下载整套） */
export function lengthOf(item) {
  const download = item.downloadName || item.downloadUrl || "";
  if (/\.(zip|docx?|pdf)$/i.test(download)) return "整套";
  if (item.id.startsWith("vid-")) {
    const minutes = durationMinutes(item.duration);
    return minutes !== null && minutes <= 10 ? "速览" : "精读";
  }
  if (moduleOf(item) === "站外链接") return "速览";
  if (moduleOf(item) === "图示板书") return "速览";
  if (item.pages && item.pages <= 6) return "速览";
  return "精读";
}
