# Gaia Frontend Functionality Checklist

This checklist compares the required Phase 1 frontend functionality with the full redesign.

## Shell And Navigation

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| Switch between IAG Summary, 5C, Sustainability, and Next Steps | Top workspace navigation and Control Dock page selector | Browser verified all 4 page buttons and page transitions |
| Keep Gaia/Yoplait project context visible | Top workspace bar and masthead badges | Browser verified Yoplait UK and active page masthead |
| Remove old sidebar-only presentation | Left sidebar removed; actions moved to right Control Dock | Browser verified `Phase 1 console` is absent and Control Dock is present |
| Preserve responsive content access | Main workspace plus sticky Control Dock on desktop, Quick Actions panel on mobile | Browser verified desktop and 390px mobile viewports |

## IAG Summary

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| Executive Summary, Company, Competition, Culture, Consumer, Category tabs | Horizontal tab strip in IAG page | Browser verified Executive Summary and Company tab switching |
| View gap type, importance, confidence, explanation, next steps | IAG content panels | Browser verified gap type and recommendations |
| Edit mode for IAG fields and save action | Control Dock Edit mode switch | Browser verified Save appears in edit mode and hides in view mode |
| Evidence accordion | IAG content area | Preserved component and visible in IAG flow |

## Backend, Evidence, And Export

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| Additional Context input | Control Dock reanalysis panel | Browser verified fill/input works |
| Upload evidence control | Control Dock reanalysis panel | Browser verified control is present; upload handler unchanged |
| Run backend analysis | Control Dock reanalysis panel | Browser verified live backend success message |
| Export Summary PDF | Control Dock action area on IAG and 5C | Browser verified action is present; export handler unchanged |
| Backend API mapping and analyzer tests | `src/lib/phase1-api.ts`, `backend/`, `tests/` | `python -m unittest discover -s tests` passed |
| Mobile quick actions | Quick Actions panel before page content | Browser verified actions appear before the main content at 390px width |

## 5C Analysis

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| 5C page entry | Top workspace navigation and Control Dock selector | Browser verified navigation to 5C |
| Job to be Done | 5C summary panel | Browser verified Job to be Done is visible |
| Company, Competition, Culture, Consumer, Category sub-tabs | 5C tab strip | Browser verified Competition tab content |
| Summarize to IAG | Control Dock action on 5C | Browser verified action is present |
| Reanalyze selected 5C module | 5C summarize panel | Browser verified Reanalyze action is present |

## Sustainability

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| Sustainability analysis view | Top workspace navigation and main content | Browser verified Sustainability content |
| Goal mix chart | Sustainability right-side chart panel | Browser verified Goal mix is visible |
| Generate new goals | Control Dock action on Sustainability | Browser verified Child Nutrition Outcome Scorecard is generated |
| Analyze goals | Control Dock reanalysis panel | Browser verified Analyze goals action is present |
| Goal editing/removal | Sustainability edit mode | Preserved component paths and handlers |

## Next Steps

| Functionality | Redesign location | Verification |
| --- | --- | --- |
| Recommendation view | Next Steps main content | Browser verified Next recommended product |
| Fullscreen recommendation modal | Next Steps Fullscreen action | Browser verified dialog opens and closes |
| Recommendation editing and save | Next Steps edit mode | Preserved component paths and handlers |

## Automated Checks

- `npm run typecheck` passed.
- `npm run build` passed.
- `python -m unittest discover -s tests` passed.
- Browser regression passed with no fresh console errors.
