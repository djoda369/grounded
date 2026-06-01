export type PageKey = "home" | "iag" | "fiveC" | "sustainability" | "next";
export type FiveCTab =
  | "summary"
  | "company"
  | "competition"
  | "culture"
  | "consumer"
  | "category";

export type EvidenceBlock = {
  title: string;
  summary: string;
  facts: string[];
  sources: string[];
  signals: string[];
  implications: string[];
};

export type GapInsight = {
  key: FiveCTab;
  label: string;
  type: string;
  importance: string;
  confidence: number;
  explanation: string;
  nextSteps: string[];
  evidence: EvidenceBlock[];
};

export type SustainabilityGoal = {
  id: string;
  title: string;
  description: string;
  category: "environmental" | "social" | "governance";
  subcategory: string;
  type: "target" | "initiative" | "policy";
  status: "planned" | "active" | "complete";
  startYear: number;
  endYear: number;
  flagship: boolean;
};

export const pageOptions: Array<{ key: PageKey; label: string }> = [
  { key: "home", label: "Home" },
  { key: "iag", label: "IAG Summary" },
  { key: "fiveC", label: "5C" },
  { key: "sustainability", label: "Sustainability" },
  { key: "next", label: "Next Steps" },
];

export const companyProfile = {
  brand: "Yoplait",
  market: "Yoplait UK",
  project: "Intention Action Gap diagnostic",
  belief:
    "We believe childhood is a critical window for bone development and that no child should suffer from preventable nutrient deficiencies like rickets in the 21st century.",
  purpose:
    "To be the positive voice for nutrition in the UK, nourishing the nation with tasty dairy goodness and protecting future bone health, especially for children at risk of calcium and vitamin D shortfalls.",
  pursuits: {
    product:
      "A lifespan-spanning portfolio of fortified yogurts, including Petits Filous and Frubes for children, expanding into high-protein and Skyr ranges for teenagers and adults.",
    platform:
      "Integrated advocacy through retail proximity, clinical-science PR, and emotional storytelling that closes the parenting knowledge-action gap around dairy and bone health.",
    impact:
      "Reverse the 10-year yogurt consumption decline, improve bone health outcomes for 1 million at-risk children, and drive GBP 150m in additional category value within five years.",
  },
};

export const strategicShifts = {
  competition: {
    from:
      "The competitive landscape clusters around mainstream, accessible dairy, broad lifestyle wellness, and natural-goodness claims. Competitors talk about everyday nutrition or ethical sourcing, but few go deep on fortified childhood nutrition.",
    to: [
      "Resolve parental uncertainty about child nutrient sufficiency and bone health.",
      "Build clinically validated differentiation around vitamin D and calcium fortification.",
      "Move from supermarket messaging to trusted advocacy through schools, health voices, and parent communities.",
      "Create long-term engagement strategies for underserved or at-risk families.",
    ],
  },
  culture: {
    from:
      "Parents are navigating a crisis of confidence in kids' dairy. Sugar reduction has become the dominant signal, but substitution into plain, adult, or plant-based formats can strip out fortification.",
    to:
      "A new standard of intentional simplicity is forming: fewer ingredients, less sugar, and clinically meaningful fortification in formats children will actually eat.",
  },
  consumer: {
    from:
      "Buyers experience a betrayal of expectations when a product tastes different, contains unexpected ingredients, or lacks promised visible fruit.",
    to:
      "Consumers expect food brands to be transparent and consistent, especially when the product carries nostalgia, family safety, and health cues.",
  },
  category: {
    from: "Nostalgic comfort with modern nutritional confidence.",
    to:
      "Anchor emotional reassurance in demonstrable nutritional advancement and transparent upgrades, using nostalgia as supporting context rather than the lead message.",
  },
  job:
    "Help UK parents confidently nourish their children's bone health by offering transparently fortified, clinically validated dairy products that deliver great taste and essential nutrients without nutritional compromise or confusion.",
};

const sharedEvidence: EvidenceBlock[] = [
  {
    title: "Nutrition-Sustainability Disconnect",
    summary:
      "The omission of measurable nutritional outcomes from sustainability commitments weakens the company's strategy of integrating health with environmental goals.",
    facts: [
      "Current sustainability commitments do not include specific nutrition outcome measurement.",
      "Childhood nutrition and bone health metrics are not yet explicit in the wider governance scorecard.",
    ],
    sources: [
      "Stakeholder feedback questions the gap between nutrition messaging and sustainability targets.",
      "Internal reviews show the product narrative is stronger than the impact measurement system.",
    ],
    signals: [
      "The public ambition references 1 million at-risk children, but the sustainability KPI set does not yet measure that outcome.",
      "Projected category value is not linked to direct health or nutritional benefits.",
    ],
    implications: [
      "The brand can lose credibility if health and sustainability are reported as separate agendas.",
      "A small set of nutrition KPIs would make the impact claim more defensible.",
    ],
  },
  {
    title: "Targeted Nutrition Drives Growth",
    summary:
      "Focused childhood nutrition interventions, measured alongside sustainability activity, can translate purpose into market differentiation.",
    facts: [
      "Childhood is a critical window for bone development.",
      "Fortified dairy products can help address calcium and vitamin D shortfalls.",
    ],
    sources: [
      "Clinical literature supports fortified dairy as a credible delivery vehicle.",
      "Pilot-style programs can validate claims with pre and post measurement.",
    ],
    signals: [
      "A focused program can improve trust among parents seeking clear health proof.",
      "Measurement can convert brand purpose into an executive-ready business case.",
    ],
    implications: [
      "The strongest commercial route is to link product quality, nutrition proof, and sustainability investment.",
      "Targeted interventions are easier to explain than broad environmental pledges.",
    ],
  },
  {
    title: "Unified Trust Messaging",
    summary:
      "A single promise that connects fortification, taste consistency, and responsible operations reduces cognitive load for parents.",
    facts: [
      "Parents want less sugar without losing the benefits of fortified dairy.",
      "Trust depends on what they can see and taste before they process wider ESG claims.",
    ],
    sources: [
      "Consumer reviews show strong sensitivity to reformulation and product consistency.",
      "Cultural analysis shows an appetite for simple, proof-backed nutrition language.",
    ],
    signals: [
      "Consistency defects can erase the value of otherwise credible health claims.",
      "Clearer packaging and retail education can turn evaluation anxiety into confidence.",
    ],
    implications: [
      "Make the nutrition promise visible at the point of purchase.",
      "Use sustainability proof as reinforcement, not a separate storyline.",
    ],
  },
];

export const iagSummary =
  "The gap is primarily strategic because the company's stated ambition blends environmental stewardship with health-led product value, but the current goal set operationalizes the environmental side far more than the nutrition side. The commitments are broad and aspirational, yet they stop short of translating the core consumer-health promise into measurable KPIs such as child bone health, fortification efficacy, or clinical outcomes. This weakens alignment between brand narrative and execution: the company is claiming integrated impact, but the measurable system is organized around sustainability activity rather than the nutritional outcomes that would substantiate the claim. The problem is reinforced by product inconsistency, which undermines trust in any health promise and makes it harder to credibly link sustainability investment to consumer benefit.";

export const gapInsights: GapInsight[] = [
  {
    key: "summary",
    label: "Executive Summary",
    type: "Strategic",
    importance: "High",
    confidence: 89,
    explanation: iagSummary,
    nextSteps: [
      "Add nutrition outcome KPIs for fortified product reach, vitamin D and calcium penetration, and child bone-health indicators.",
      "Tie the 1 million children ambition to a funded plan with partners, geographies, baselines, and annual milestones.",
      "Stabilize formulations and quality control so taste and texture support the nutritional proposition.",
      "Publish an integrated scorecard connecting environmental delivery, product consistency, and health outcomes.",
      "Run pilot programs with pre and post health measurement.",
    ],
    evidence: sharedEvidence,
  },
  {
    key: "company",
    label: "Company",
    type: "Strategic",
    importance: "High",
    confidence: 83,
    explanation:
      "The core mismatch is strategic: the company's stated purpose emphasizes child nutrition and positive health impact, but its sustainability commitments are organized around broader environmental and governance priorities rather than direct health outcomes. Even where commitments are relevant, they are not yet tied to health-specific metrics, accountability, or operational pathways that convert ambition into tangible consumer and societal impact.",
    nextSteps: [
      "Make child nutrition a named pillar inside the sustainability system.",
      "Add a health-outcome owner and review cadence.",
      "Connect product innovation briefs to the purpose and impact scorecard.",
    ],
    evidence: sharedEvidence,
  },
  {
    key: "competition",
    label: "Competition",
    type: "Strategic",
    importance: "High",
    confidence: 84,
    explanation:
      "The main gap is not a lack of ambition, but a mismatch between a tightly focused commercial thesis and a very broad sustainability agenda. The business can win through specific, evidence-led childhood nutrition advocacy, yet the sustainability platform spans climate, biodiversity, water, waste, DEI, community, and policy outcomes. That breadth risks diluting execution attention.",
    nextSteps: [
      "Prioritize the commitments that strengthen the nutrition-led competitive position.",
      "Convert broad ESG goals into proof points a parent can understand.",
      "Use competitors' general wellness messaging as the contrast point.",
    ],
    evidence: sharedEvidence,
  },
  {
    key: "culture",
    label: "Culture",
    type: "Strategic",
    importance: "High",
    confidence: 87,
    explanation:
      "The company is trying to occupy a trust position that depends on simplicity, proof, and consistency, while its current posture is fragmented across separate product stories, campaigns, and long-dated sustainability pledges. Culturally, parents want quick proof that a product is good for their child; strategically, the company asks them to process lower sugar, fortification, convenience, advocacy, and broad sustainability leadership all at once.",
    nextSteps: [
      "Build a single cultural narrative around intentional simplicity.",
      "Show how reformulation and fortification can coexist.",
      "Move evidence into retail, packaging, and parent-facing education.",
    ],
    evidence: sharedEvidence,
  },
  {
    key: "consumer",
    label: "Consumer",
    type: "Strategic",
    importance: "High",
    confidence: 88,
    explanation:
      "The company's purpose relies on credibility in nutrition and care, but buyers judge that promise through sensory and ingredient experience first. When reformulations are perceived as worse, or labelled attributes are not visibly delivered, the health mission is weakened before any educational or sustainability narrative can matter.",
    nextSteps: [
      "Audit negative review themes and map them to product and messaging fixes.",
      "Use sensory consistency as a trust KPI.",
      "Bring ingredient proof into the first evaluation moment.",
    ],
    evidence: sharedEvidence,
  },
  {
    key: "category",
    label: "Category",
    type: "Strategic",
    importance: "High",
    confidence: 88,
    explanation:
      "The company is trying to advance a wide sustainability and advocacy agenda while the category's main job is to deliver credible, science-backed nutrition benefits. The current mix of emotional heritage cues and broad sustainability commitments does not sufficiently reinforce the category's core promise of measurable child health improvement.",
    nextSteps: [
      "Lead with the nutrition job to be done.",
      "Use sustainability commitments as reasons to believe in the brand's stewardship.",
      "Make category need states visible in prioritization and reporting.",
    ],
    evidence: sharedEvidence,
  },
];

export const competitors = [
  {
    name: "Muller Group",
    selected: true,
    position:
      "High-quality, broadly accessible dairy products that deliver everyday nutrition and moments of pleasure for mainstream consumers.",
    purpose:
      "Create dairy products that nourish and delight, promoting a healthier lifestyle for everyone.",
    profit:
      "Yoplait can carve out a premium niche by emphasizing childhood bone health, targeted fortification, and emotionally resonant advocacy.",
  },
  {
    name: "Danone UK",
    selected: false,
    position:
      "A health and wellbeing platform with broad yogurt, plant-based, and probiotic credibility.",
    purpose:
      "Bring health through food to as many people as possible while signaling responsible production.",
    profit:
      "Yoplait should avoid a generic wellness battle and focus on child-specific nutrition proof.",
  },
  {
    name: "Arla Foods",
    selected: true,
    position:
      "Farmer-owned dairy, naturalness, animal welfare, and sustainability credibility.",
    purpose:
      "Champion natural dairy and responsible farming for better everyday food.",
    profit:
      "Yoplait can separate from provenance-led claims by proving nutritional outcomes.",
  },
  {
    name: "Yeo Valley",
    selected: true,
    position:
      "Organic, nature-positive dairy rooted in rural authenticity and responsible farming.",
    purpose:
      "Offer organic food that is good for people, farming, and the land.",
    profit:
      "Yoplait can own fortification and parent reassurance where organic cues alone do not solve the nutrient gap.",
  },
];

export const culturalDrivers = [
  {
    title: "The Fortification Gap No One Is Talking About",
    selected: true,
    confidence: 93,
    observation:
      "Nearly 20% of UK children aged 4-10 are deficient in vitamin D, while declining kids' yogurt consumption means more children are missing targeted calcium and vitamin D fortification.",
    tension:
      "Parents reaching for cleaner plain or adult Greek yogurts to avoid sugar may remove the fortification that matters most at this life stage.",
    people:
      "Parents are making well-intentioned trade-offs without realizing the nutrient consequence.",
    implication:
      "Make fortification legible and urgent at the point of purchase, especially for the 4-10 age window.",
    sources: ["Public health reporting", "Category consumption analysis", "Yoplait planning data"],
  },
  {
    title: "Sugar Fear Is Driving Parents Away From the Nutrients Their Kids Need",
    selected: true,
    confidence: 89,
    observation:
      "The sugar conversation has taught parents what to avoid, but not what nutrients they still need to replace.",
    tension:
      "Avoidance is winning over informed substitution.",
    people:
      "Parents feel responsible when they reduce sugar, even when the replacement is nutritionally weaker.",
    implication:
      "Pair lower sugar messaging with explicit calcium and vitamin D reassurance.",
    sources: ["Parent sentiment", "Retail category shifts", "Nutrition education sources"],
  },
  {
    title: "The Convenience Premium",
    selected: true,
    confidence: 86,
    observation:
      "Portable formats are increasingly interpreted as a health signal when they help children eat better during busy routines.",
    tension:
      "Convenience can look processed unless backed by ingredient clarity.",
    people:
      "Parents want frictionless nutrition they can trust in school bags and after-school moments.",
    implication:
      "Frame portable fortified formats as a disciplined nutrition habit, not a treat shortcut.",
    sources: ["Shopper journey mapping", "Convenience food trend reports"],
  },
  {
    title: "Half of Parents Already Think They're Failing",
    selected: true,
    confidence: 82,
    observation:
      "Parents are overwhelmed by conflicting nutrition advice and respond to brands that reduce guilt with useful proof.",
    tension:
      "Education helps only if it feels practical rather than judgmental.",
    people:
      "Parents need reassurance and specific actions, not abstract health lectures.",
    implication:
      "Use warm authority and small confident choices as the communication posture.",
    sources: ["Parent community comments", "Health literacy reports"],
  },
];

export const consumerStages = [
  {
    stage: "Discovery",
    selected: true,
    definition:
      "The first moment someone becomes aware of the brand or category. Content should create exposure, spark curiosity, and introduce the brand in a memorable way.",
    barrier:
      "Physical availability gaps and negative bioengineered disclosure moments can turn first impressions into rejection before trial.",
    reviews: [
      "I wanted to buy it for the kids, but it was not in my store.",
      "The label made me pause. I did not know what to trust.",
    ],
  },
  {
    stage: "Salience",
    selected: false,
    definition:
      "The degree to which the brand feels relevant to a shopper's life and priorities.",
    barrier:
      "Yoplait can feel nostalgic but not always actively relevant to today's parent nutrition concerns.",
    reviews: ["I remember it from childhood, but I am not sure it is what I want now."],
  },
  {
    stage: "Evaluation",
    selected: true,
    definition:
      "The point where shoppers compare claims, ingredients, taste expectations, and alternatives.",
    barrier:
      "Buyers experience a betrayal of expectations when taste, ingredients, or visible fruit do not match the promise.",
    reviews: [
      "It tastes different now and not in a good way.",
      "I expected more fruit and a cleaner ingredient list.",
    ],
  },
  {
    stage: "Choice",
    selected: true,
    definition:
      "The final influence that converts consideration into purchase.",
    barrier:
      "At shelf, parents need fast proof that fortified yogurt is the better choice than plain or plant-based alternatives.",
    reviews: ["I chose another brand because I could understand the benefits faster."],
  },
  {
    stage: "Commitment",
    selected: false,
    definition: "The pattern that turns one purchase into a repeat habit.",
    barrier:
      "Inconsistent quality makes repeat purchase fragile, even when the brand mission is appealing.",
    reviews: ["My kids liked one box and rejected the next."],
  },
  {
    stage: "Advocacy",
    selected: false,
    definition: "The reasons a buyer recommends or defends the brand.",
    barrier:
      "Advocacy depends on confidence that the brand is honest, consistent, and meaningfully better for children.",
    reviews: ["I would recommend it if I felt the health claims were clearer."],
  },
];

export const needStates = [
  {
    name: "Childhood Bone Health & Rickets Prevention",
    selected: true,
    score: 94,
    description:
      "Parents of children aged 4-10 need a trusted fortified daily food source that contributes to calcium and vitamin D intake during the critical developmental window.",
  },
  {
    name: "Ingredient Trust & Label Transparency",
    selected: true,
    score: 86,
    description:
      "Parents need labels and claims that quickly explain what changed, why it changed, and what benefit remains.",
  },
  {
    name: "Nutritional Myth-Busting & Category Rehabilitation",
    selected: true,
    score: 82,
    description:
      "The category needs to recover from oversimplified sugar narratives by explaining nutrient trade-offs more clearly.",
  },
  {
    name: "Nostalgic Comfort with Modern Nutritional Confidence",
    selected: true,
    score: 78,
    description:
      "Families want familiar yogurt experiences upgraded with current nutrition proof and better transparency.",
  },
  {
    name: "Total Family & Lifespan Nourishment",
    selected: false,
    score: 64,
    description:
      "A broader portfolio role that spans children, teenagers, and adults without losing the child-health anchor.",
  },
];

export const initialGoals: SustainabilityGoal[] = [
  {
    id: "decarbonisation",
    title: "Accelerated Decarbonisation and Net-Zero Emissions Roadmap",
    description:
      "Implement advanced decarbonisation technologies and integrated climate strategies to reduce Scope 1, 2, and 3 emissions, track progress with science-based targets, and reach a net-zero milestone by 2040 with critical targets for 2030.",
    category: "environmental",
    subcategory: "climate change",
    type: "target",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "nature",
    title: "Ecosystem Restoration and Nature Regeneration Initiative",
    description:
      "Restore, conserve, and sustainably manage two hectares of forested land for every one hectare used by operations, moving beyond tree counts into ecosystem restoration.",
    category: "environmental",
    subcategory: "biodiversity",
    type: "target",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "circularity",
    title: "Zero Waste & Circular Product Lifecycle Transformation",
    description:
      "Establish closed-loop systems that divert product waste from landfill and integrate circular design principles to substitute virgin plastics with recycled or upcycled alternatives.",
    category: "environmental",
    subcategory: "circular economy",
    type: "target",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "water",
    title: "Advanced Water Stewardship and Efficiency Optimization",
    description:
      "Implement water efficiency technologies and recycling practices at service centres and production facilities, particularly in water-stressed regions.",
    category: "environmental",
    subcategory: "water resources",
    type: "initiative",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "innovation",
    title: "Integrated Circular Product Innovation & Lifecycle Assessment",
    description:
      "Embed circular design principles in new product development by integrating lifecycle assessments, durability, reusability, and material recovery.",
    category: "environmental",
    subcategory: "product innovation",
    type: "initiative",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "safety",
    title: "Employee Safety, Wellbeing, and Zero Harm Transformation",
    description:
      "Move toward a proactive safety framework using LTIFR as a key metric while improving health, safety, and wellbeing programs across operations.",
    category: "social",
    subcategory: "health and safety",
    type: "initiative",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "dei",
    title: "Accelerating Diversity, Equity, and Inclusion for Sustainable Growth",
    description:
      "Increase female leadership, double representation in service centres, and improve inclusivity ratings through employee resource groups and targeted policies.",
    category: "social",
    subcategory: "diversity and inclusion",
    type: "target",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "community",
    title: "Community Resilience & Food Security Empowerment Program",
    description:
      "Expand food rescue and distribution networks to serve more people annually while supporting crisis response and long-term community resilience.",
    category: "social",
    subcategory: "community",
    type: "initiative",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
  {
    id: "policy",
    title: "Global Sustainability Policy Leadership & Advocacy Commitment",
    description:
      "Establish a policy engagement function to advocate for sustainable and circular economy policies globally and educate circular change-makers.",
    category: "governance",
    subcategory: "policy impact",
    type: "policy",
    status: "planned",
    startYear: 2025,
    endYear: 2030,
    flagship: true,
  },
];

export const recommendation = {
  title: "Sustainagility Strategy",
  bestFor:
    "Senior corporate leaders, brand strategists, and sustainability professionals in sectors focused on commercial excellence and positive social impact.",
  headline: "Empowering purpose-driven growth through sustainable innovation.",
  overview:
    "The Sustainagility Strategy approach interweaves corporate, brand, and social purpose with tangible business objectives. It reframes sustainability as a growth engine by aligning a clear narrative, positioning architecture, activation roadmap, and measurable environmental and social outcomes.",
  outcomes: [
    "Drives growth by aligning sustainability with business objectives and converting purpose into competitive advantage.",
    "Enhances stakeholder engagement through transparent impact measurement and sharper narratives.",
    "Inspires innovation by integrating sustainability into the brand's core identity and market differentiation.",
  ],
};
