from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Experiment:
    id: str
    title: str
    summary: str
    image: str
    image_alt: str


@dataclass(frozen=True)
class Topic:
    number: int
    slug: str
    title: str
    experiments: tuple[Experiment, ...]


@dataclass(frozen=True)
class Level:
    slug: str
    label: str
    topics: tuple[Topic, ...]


@dataclass(frozen=True)
class Subject:
    slug: str
    label: str
    levels: tuple[Level, ...]


def _slug(value: str) -> str:
    normalized = value.lower().replace("(ii)", "ii").replace("(iii)", "iii")
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


def _level(slug: str, label: str, topics: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]) -> Level:
    level_topics = []
    prefix = "o" if slug == "o-level" else "a"
    for topic_number, (title, raw_experiments) in enumerate(topics, start=1):
        topic_slug = _slug(title)
        experiments = tuple(
            Experiment(
                id=f"{prefix}-{topic_number:02d}-{_slug(experiment_title)}",
                title=experiment_title,
                summary=summary,
                image=f"assets/chemistry/{slug}/{topic_number}/{prefix}-{topic_number:02d}-{_slug(experiment_title)}.webp",
                image_alt=f"Fallback apparatus illustration for {experiment_title}.",
            )
            for experiment_title, summary in raw_experiments
        )
        level_topics.append(Topic(topic_number, topic_slug, title, experiments))
    return Level(slug, label, tuple(level_topics))


CHEMISTRY = Subject(
    slug="chemistry",
    label="Chemistry",
    levels=(
        _level(
            "o-level",
            "Ordinary Level",
            (
                (
                    "Basic laboratory techniques",
                    (
                        ("Measuring liquid volumes", "Use a measuring cylinder and pipette correctly, then compare their precision."),
                        ("Measuring mass", "Use a balance to measure sample mass and record an appropriate precision."),
                        ("Measuring temperature", "Measure and record temperature changes with a laboratory thermometer."),
                        ("Filtration", "Separate an insoluble solid from a liquid using filter paper and a funnel."),
                        ("Evaporation", "Recover a dissolved solid by carefully evaporating the solvent."),
                        ("Crystallisation", "Prepare crystals from a saturated solution by controlled cooling and evaporation."),
                        ("Simple distillation", "Separate a volatile solvent from a solution using a simple distillation apparatus."),
                        ("Fractional distillation", "Separate miscible liquids with different boiling points using a fractionating column."),
                        ("Paper chromatography", "Separate a mixture of soluble dyes and compare their movement on paper."),
                        ("Separate sand and salt", "Dissolve, filter and evaporate a mixture to recover both components."),
                        ("Separate iron and sulphur", "Use a magnet and physical properties to separate iron from sulphur."),
                    ),
                ),
                (
                    "Acid-base titrations",
                    (
                        ("Standardise sodium hydroxide with hydrochloric acid", "Titrate measured solutions to determine the concentration of sodium hydroxide."),
                        ("Choose an acid-base indicator", "Compare methyl orange and phenolphthalein transition ranges for an acid-base endpoint."),
                        ("Calculate an unknown concentration", "Use a balanced equation and mean titre to calculate an unknown solution concentration."),
                        ("Calculate solute mass from a titre", "Convert titration results into the amount and mass of solute in a sample."),
                        ("Determine percentage purity by titration", "Use a titration result to calculate the proportion of active substance in a sample."),
                    ),
                ),
                (
                    "Preparation of salts",
                    (
                        ("Copper(II) sulphate from copper(II) oxide", "Warm dilute sulphuric acid with excess copper(II) oxide, then filter and crystallise."),
                        ("Copper(II) sulphate from copper(II) carbonate", "React copper(II) carbonate with dilute sulphuric acid, then filter and crystallise."),
                        ("Zinc sulphate crystals", "Prepare a soluble zinc salt from dilute sulphuric acid and an excess zinc compound."),
                        ("Sodium chloride crystals", "Prepare sodium chloride by neutralisation and crystallise the resulting solution."),
                        ("Lead(II) iodide by precipitation", "Mix suitable soluble salts to form and isolate a yellow lead(II) iodide precipitate."),
                        ("Barium sulphate by precipitation", "Combine soluble barium and sulphate solutions and collect the insoluble precipitate."),
                        ("Calcium carbonate by precipitation", "Mix soluble calcium and carbonate solutions and isolate calcium carbonate."),
                        ("Water of crystallisation", "Heat hydrated crystals, measure the mass change and infer water of crystallisation."),
                    ),
                ),
                (
                    "Qualitative analysis",
                    (
                        ("Test aluminium ions", "Use sodium hydroxide and aqueous ammonia to observe aluminium hydroxide behaviour."),
                        ("Test zinc ions", "Compare zinc hydroxide formation and dissolution in excess sodium hydroxide and ammonia."),
                        ("Test lead(II) ions", "Use sodium hydroxide and aqueous ammonia to examine the characteristic lead(II) precipitate."),
                        ("Test calcium ions", "Use reagent observations to distinguish calcium ions from other common cations."),
                        ("Test magnesium ions", "Observe the precipitate formed when magnesium ions react with aqueous alkali."),
                        ("Test copper(II) ions", "Identify copper(II) ions from their characteristic blue precipitate and ammonia complex."),
                        ("Test iron(II) ions", "Observe the green iron(II) hydroxide precipitate and its change on standing."),
                        ("Test iron(III) ions", "Identify iron(III) ions from the characteristic reddish-brown hydroxide precipitate."),
                        ("Test ammonium ions", "Warm the sample with alkali and test for ammonia gas using damp indicator paper."),
                        ("Test carbonate ions", "Add dilute acid and identify the carbon dioxide released using limewater."),
                        ("Test sulphate ions", "Acidify the sample and use a barium salt solution to test for sulphate."),
                        ("Test chloride ions", "Acidify with dilute nitric acid and test for a silver chloride precipitate."),
                        ("Test nitrate ions", "Use the prescribed nitrate test and record the characteristic positive observation."),
                        ("Test sulphite ions", "Add dilute acid and identify the sulphur dioxide released with a suitable test."),
                        ("Test hydrogen gas", "Use a lighted splint safely at the mouth of a test tube and listen for a squeaky pop."),
                        ("Test oxygen gas", "Insert a glowing splint and observe whether it relights."),
                        ("Test carbon dioxide", "Bubble the gas through limewater and observe the change."),
                        ("Test ammonia gas", "Use damp red litmus paper to identify alkaline ammonia gas."),
                        ("Test chlorine gas", "Use damp indicator paper to observe chlorine's bleaching action under supervision."),
                        ("Test sulphur dioxide", "Use a suitable reagent to identify the reducing action of sulphur dioxide."),
                        ("Test for water vapour", "Use anhydrous copper(II) sulphate or cobalt chloride paper to detect water."),
                        ("Flame tests", "Compare flame colours from clean wire-loop samples to identify selected metal ions."),
                    ),
                ),
                (
                    "Reactions of common substances",
                    (
                        ("Heat metal carbonates", "Heat selected metal carbonates and test the gas and solid products."),
                        ("Heat metal nitrates", "Compare thermal decomposition observations for selected metal nitrates."),
                        ("Heat metal hydroxides", "Heat selected metal hydroxides and observe changes in the residue and vapour."),
                        ("Reactivity series and displacement", "Compare metal displacement reactions to infer relative reactivity."),
                        ("Acids with metals", "React selected metals with dilute acid and compare gas production and reaction rate."),
                        ("Acids with carbonates", "React a carbonate with dilute acid and identify the carbon dioxide produced."),
                        ("Acids with bases", "Neutralise an acid with a base and use an indicator to observe the endpoint."),
                        ("Properties of metal oxides", "Classify selected oxides as acidic, basic or amphoteric from their reactions."),
                    ),
                ),
                (
                    "Rates of reaction",
                    (
                        ("Sodium thiosulphate and hydrochloric acid: concentration", "Vary concentration and time the disappearance of a marked cross."),
                        ("Sodium thiosulphate and hydrochloric acid: temperature", "Vary temperature and compare the time for the reaction cloudiness endpoint."),
                        ("Marble chips and hydrochloric acid: surface area", "Compare gas-production rates for marble chips of different sizes."),
                        ("Catalytic decomposition of hydrogen peroxide", "Use manganese(IV) oxide to catalyse oxygen production from hydrogen peroxide."),
                    ),
                ),
                (
                    "Energy changes",
                    (
                        ("Enthalpy of neutralisation", "Measure the temperature change when an acid and alkali react in an insulated cup."),
                        ("Enthalpy of solution: ammonium nitrate", "Measure the temperature change as ammonium nitrate dissolves in water."),
                        ("Enthalpy of solution: sodium hydroxide", "Measure the temperature change as sodium hydroxide dissolves in water."),
                        ("Enthalpy of combustion of an alcohol", "Burn a measured alcohol sample to heat water and estimate energy released per mole."),
                    ),
                ),
                (
                    "Electrolysis",
                    (
                        ("Copper(II) sulphate with inert electrodes", "Electrolyse copper(II) sulphate using inert electrodes and identify electrode products."),
                        ("Copper(II) sulphate with copper electrodes", "Observe how copper electrodes change during electrolysis of copper(II) sulphate."),
                        ("Electroplating", "Deposit a thin metal coating on an object using a controlled electrolytic cell."),
                        ("Electrolysis of brine", "Investigate products at the electrodes during electrolysis of concentrated sodium chloride solution."),
                        ("Electrolysis of acidified water", "Decompose acidified water and compare the volumes of gases at the electrodes."),
                    ),
                ),
                (
                    "Air, water and corrosion",
                    (
                        ("Percentage of oxygen in air", "Use a reaction that removes oxygen and measure the resulting volume decrease."),
                        ("Conditions for rusting", "Compare iron exposed to water and oxygen under controlled conditions."),
                        ("Hard and soft water: soap test", "Compare lather formation and scum in hard and soft water samples."),
                    ),
                ),
                (
                    "Organic chemistry",
                    (
                        ("Test for unsaturation with bromine water", "Add bromine water to an organic sample and observe decolourisation."),
                        ("Test for unsaturation with acidified permanganate", "Use acidified potassium permanganate to test an organic sample for unsaturation."),
                        ("Tests for alcohols", "Apply suitable qualitative reactions to identify an alcohol functional group."),
                        ("Tests for carboxylic acids", "Use indicator and carbonate reactions to identify a carboxylic acid."),
                        ("Soap preparation by saponification", "Heat a fat or oil with alkali and isolate the soap product safely."),
                        ("Fermentation of glucose", "Monitor carbon dioxide production during yeast fermentation of glucose solution."),
                    ),
                ),
            ),
        ),
        _level(
            "a-level",
            "Advanced Level",
            (
                (
                    "Volumetric analysis",
                    (
                        ("Strong acid-base titration", "Use a standard solution and indicator endpoint to determine an unknown concentration."),
                        ("Weak acid-strong base titration", "Record the titration curve and identify the buffer region and equivalence point."),
                        ("Double-indicator carbonate titration", "Use two indicator endpoints to analyse a sodium carbonate and hydrogencarbonate mixture."),
                        ("Back titration of calcium carbonate", "Add excess standard acid to a carbonate sample and titrate the remaining acid."),
                        ("Permanganate titration of iron(II)", "Titrate iron(II) with acidified potassium permanganate to a persistent endpoint."),
                        ("Permanganate titration of ethanedioate", "Use a heated acidic ethanedioate solution in a redox titration with permanganate."),
                        ("Permanganate titration of hydrogen peroxide", "Determine hydrogen peroxide concentration by titration with acidified permanganate."),
                        ("Iodometric analysis of copper(II)", "Liberate iodine from a copper(II) sample and titrate it with thiosulphate."),
                        ("Iodometric analysis of bleach", "Use iodine liberation and thiosulphate titration to estimate available chlorine in bleach."),
                        ("Iodometric analysis of vitamin C", "Determine vitamin C content from its reaction with iodine and a starch endpoint."),
                        ("Dilution of a standard solution", "Prepare a target concentration by accurate dilution using volumetric glassware."),
                        ("Prepare a primary standard solution", "Weigh, dissolve and dilute a primary standard to a known concentration."),
                    ),
                ),
                (
                    "Thermochemistry",
                    (
                        ("Enthalpy of neutralisation", "Measure a neutralisation temperature change and calculate molar enthalpy change."),
                        ("Enthalpy of solution", "Measure the thermal effect of dissolving a known amount of solute in water."),
                        ("Enthalpy of displacement", "Use a displacement reaction temperature change to calculate enthalpy change."),
                        ("Enthalpy of combustion", "Use a spirit burner calorimetry setup to estimate molar enthalpy of combustion."),
                        ("Hess cycle: magnesium oxide", "Combine measured reaction enthalpies for magnesium routes to estimate formation enthalpy."),
                    ),
                ),
                (
                    "Chemical kinetics",
                    (
                        ("Iodine clock reaction", "Vary reactant conditions and time the sudden appearance of the iodine-starch colour."),
                        ("Acidified propanone and iodine: reaction order", "Use concentration and time data to infer reaction orders for the iodination reaction."),
                        ("Temperature and activation energy", "Measure rates at several temperatures and analyse the Arrhenius relationship."),
                        ("Decomposition of hydrogen peroxide", "Measure oxygen evolution to investigate the rate of hydrogen peroxide decomposition."),
                    ),
                ),
                (
                    "Chemical equilibrium",
                    (
                        ("Equilibrium constant of esterification", "Analyse an esterification mixture at equilibrium to estimate its equilibrium constant."),
                        ("Iron(III)-thiocyanate equilibrium", "Change concentration or temperature and observe the equilibrium colour shift."),
                        ("Partition coefficient", "Measure how a solute distributes between two immiscible liquid phases."),
                        ("Dissociation constant of a weak acid", "Measure pH at known concentrations to estimate the acid dissociation constant."),
                        ("Buffer solution behaviour", "Compare pH changes in a buffer and water after small acid or alkali additions."),
                    ),
                ),
                (
                    "Electrochemistry",
                    (
                        ("Daniell cell electrode potentials", "Construct a zinc-copper cell and measure its voltage under controlled conditions."),
                        ("Faraday constant by electrolysis", "Relate charge passed to deposited or liberated material to estimate Faraday's constant."),
                    ),
                ),
                (
                    "Qualitative inorganic analysis",
                    (
                        ("Test nickel(II) ions", "Use characteristic precipitate and complex-ion reactions to identify nickel(II)."),
                        ("Test manganese(II) ions", "Observe manganese(II) reactions with alkali and suitable confirmatory reagents."),
                        ("Test chromium(III) ions", "Use amphoteric hydroxide behaviour and colour changes to identify chromium(III)."),
                        ("Test cobalt(II) ions", "Compare cobalt(II) precipitate and complex-ion colours with selected reagents."),
                        ("Halide tests with silver nitrate and ammonia", "Use silver halide precipitates and ammonia solubility to distinguish halide ions."),
                        ("Transition-metal complex colours", "Add ligands to transition-metal ions and record characteristic complex colour changes."),
                        ("Group II trend experiments", "Compare selected Group II reactions and solubilities to observe down-group trends."),
                        ("Group VII trend experiments", "Compare halogen displacement reactions to investigate oxidising power down the group."),
                    ),
                ),
                (
                    "Organic functional group tests",
                    (
                        ("Carbonyl test with 2,4-DNPH", "Use 2,4-dinitrophenylhydrazine to test for aldehyde or ketone carbonyl groups."),
                        ("Aldehyde test with Tollens' reagent", "Warm a sample with Tollens' reagent and observe the silver mirror test result."),
                        ("Aldehyde test with Fehling's solution", "Warm the sample with Fehling's solution and observe formation of a brick-red precipitate."),
                        ("Iodoform test", "Use iodine and alkali to test for suitable methyl carbonyl or alcohol structures."),
                        ("Lucas test for alcohols", "Compare turbidity times with Lucas reagent to distinguish alcohol classes."),
                        ("Phenol test with bromine water", "Add bromine water to phenol and observe decolourisation and precipitate formation."),
                        ("Phenol test with iron(III) chloride", "Add iron(III) chloride solution and observe the characteristic phenol colour reaction."),
                        ("Carboxylic acid test with hydrogencarbonate", "Add sodium hydrogencarbonate and identify carbon dioxide effervescence."),
                        ("Hydrolysis of esters and halogenoalkanes", "Compare hydrolysis products and test the ions or functional groups formed."),
                        ("Tests for amines", "Use basicity and suitable reactions to identify an amine functional group."),
                        ("Tests for amides", "Hydrolyse an amide under suitable conditions and test for the products."),
                    ),
                ),
                (
                    "Organic preparations and techniques",
                    (
                        ("Aspirin synthesis", "Prepare crude aspirin by acetylating salicylic acid, then isolate and purify the product."),
                        ("Esterification", "Heat an alcohol and carboxylic acid with catalyst and identify the ester product."),
                        ("Preparation of a halogenoalkane", "Prepare a halogenoalkane using an appropriate substitution reaction and isolate it safely."),
                        ("Reflux technique", "Set up a reflux condenser to heat a reaction mixture without losing volatile material."),
                        ("Distillation technique", "Separate and collect a liquid product using a correctly assembled distillation apparatus."),
                        ("Recrystallisation", "Purify an impure solid by dissolution in hot solvent and controlled crystal formation."),
                        ("Melting point determination", "Measure a solid's melting range and use it to assess identity and purity."),
                    ),
                ),
                (
                    "Physical measurements",
                    (
                        ("Solubility curve", "Measure solubility at different temperatures and plot a solubility curve."),
                        ("Molar volume of a gas", "React magnesium with acid, collect hydrogen and calculate molar gas volume."),
                        ("Molar mass determination", "Use measured mass and amount of substance from a gas or solution experiment to estimate molar mass."),
                        ("Thermal decomposition mass loss", "Heat a compound to constant mass and use mass loss to calculate composition."),
                    ),
                ),
            ),
        ),
    ),
)


def level_by_slug(slug: str) -> Level | None:
    return next((level for level in CHEMISTRY.levels if level.slug == slug), None)


def topic_by_route(level_slug: str, topic_number: int) -> Topic | None:
    level = level_by_slug(level_slug)
    if not level:
        return None
    return next((topic for topic in level.topics if topic.number == topic_number), None)


def experiment_by_route(level_slug: str, topic_number: int, experiment_id: str) -> tuple[Topic, Experiment] | None:
    topic = topic_by_route(level_slug, topic_number)
    if not topic:
        return None
    experiment = next((item for item in topic.experiments if item.id == experiment_id), None)
    return (topic, experiment) if experiment else None