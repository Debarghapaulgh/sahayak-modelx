"""
Full NCERT Curriculum Catalog Registry (Classes 6 through 12).
Covers STEM & Social Science subjects.
"""

from typing import List, Dict, Any
from synthetictutor.core.schemas import Concept, Misconception
from synthetictutor.knowledge.graph import KnowledgeGraph

NCERT_CATALOG: List[Dict[str, Any]] = [
    # CLASS 6 - 8 GENERAL SCIENCE & MATH
    {"id": "c6_sci_motion", "name": "Motion and Measurement of Distances", "subject": "Science", "class": "Class 6", "desc": "Standard units of length, rectilinear and circular motion", "misc": "Believes motion depends on observer position without reference frames"},
    {"id": "c6_sci_light", "name": "Light, Shadows and Reflections", "subject": "Science", "class": "Class 6", "desc": "Light travels in straight lines, pinhole camera, transparent/opaque materials", "misc": "Believes vision occurs by light shooting out of human eyes"},
    {"id": "c6_sci_elec", "name": "Electricity and Circuits", "subject": "Science", "class": "Class 6", "desc": "Electric cell, bulb, closed loop circuits, conductors and insulators", "misc": "Believes electricity flows into a bulb like water into a bucket without returning"},
    {"id": "c7_sci_heat", "name": "Heat and Temperature", "subject": "Science", "class": "Class 7", "desc": "Conduction, convection, radiation, clinical and laboratory thermometers", "misc": "Confuses heat energy with temperature degree"},
    {"id": "c7_sci_acid", "name": "Acids, Bases and Salts", "subject": "Science", "class": "Class 7", "desc": "Litmus indicator, pH scale, neutralization reaction in stomach", "misc": "Believes all acids are synthetic toxic liquids"},
    {"id": "c8_sci_force", "name": "Force and Pressure", "subject": "Science", "class": "Class 8", "desc": "Contact and non-contact forces, atmospheric pressure, liquid pressure", "misc": "Believes force is a property stored inside objects"},
    {"id": "c8_sci_fric", "name": "Friction & Lubrication", "subject": "Science", "class": "Class 8", "desc": "Static, sliding, rolling friction, drag in fluids, ball bearings", "misc": "Believes friction only opposes motion and has no beneficial uses"},

    # CLASS 9 & 10 SCIENCE & MATH
    {"id": "c9_phys_motion", "name": "Motion & Kinematics", "subject": "Physics", "class": "Class 9", "desc": "Distance vs displacement, speed vs velocity, acceleration equations", "misc": "Believes zero acceleration implies an object must be at rest"},
    {"id": "c9_phys_laws", "name": "Force and Laws of Motion", "subject": "Physics", "class": "Class 9", "desc": "Newton's 1st, 2nd, and 3rd laws of motion, momentum conservation", "misc": "Believes action and reaction forces cancel out on the same body"},
    {"id": "c9_phys_grav", "name": "Gravitation & Free Fall", "subject": "Physics", "class": "Class 9", "desc": "Universal law of gravitation, g vs G, mass vs weight, buoyancy", "misc": "Believes astronauts in orbit experience zero gravitational pull"},
    {"id": "c9_phys_work", "name": "Work and Energy", "subject": "Physics", "class": "Class 9", "desc": "Work done, kinetic and potential energy, law of energy conservation", "misc": "Believes pushing against a stationary wall does physical work"},
    {"id": "c9_chem_matter", "name": "Matter in Our Surroundings", "subject": "Chemistry", "class": "Class 9", "desc": "Solids, liquids, gases, latent heat of vaporization, sublimation", "misc": "Believes gas particles stop moving when cooled"},
    {"id": "c9_chem_atoms", "name": "Atoms and Molecules", "subject": "Chemistry", "class": "Class 9", "desc": "Law of definite proportions, atomic mass unit, chemical formula writing", "misc": "Believes compounds retain the exact physical properties of constituent elements"},
    {"id": "c9_bio_cell", "name": "The Fundamental Unit of Life (Cell)", "subject": "Biology", "class": "Class 9", "desc": "Plasma membrane, nucleus, organelle functions, plant vs animal cells", "misc": "Believes plant cells do not have cell membranes"},
    
    {"id": "c10_phys_light", "name": "Light - Reflection & Refraction", "subject": "Physics", "class": "Class 10", "desc": "Mirror and lens formula, refractive index, Snell's law, total internal reflection", "misc": "Believes light bends toward normal when entering a rarer medium"},
    {"id": "c10_phys_elec", "name": "Electricity & Ohm's Law", "subject": "Physics", "class": "Class 10", "desc": "Resistance, resistivity, series and parallel circuits, Joule heating", "misc": "Believes electric current is consumed by light bulbs"},
    {"id": "c10_chem_react", "name": "Chemical Reactions and Equations", "subject": "Chemistry", "class": "Class 10", "desc": "Combination, decomposition, displacement, redox reactions, balancing", "misc": "Believes rust is formed by water drying on iron without oxygen"},
    {"id": "c10_chem_carbon", "name": "Carbon and Its Compounds", "subject": "Chemistry", "class": "Class 10", "desc": "Covalent bonding, allotropes of carbon, alkanes, alkenes, alkynes, functional groups", "misc": "Believes diamond and graphite are different chemical elements"},
    {"id": "c10_bio_life", "name": "Life Processes", "subject": "Biology", "class": "Class 10", "desc": "Autotrophic nutrition, human digestive system, double circulation in heart, nephron excretion", "misc": "Believes deoxygenated blood is blue in veins"},
    {"id": "c10_bio_heredity", "name": "Heredity and Evolution", "subject": "Biology", "class": "Class 10", "desc": "Mendelian monohybrid and dihybrid cross, dominant vs recessive alleles", "misc": "Believes dominant traits are always more frequent in human populations"},

    # CLASS 11 & 12 PHYSICS, CHEMISTRY & BIOLOGY
    {"id": "c11_phys_vectors", "name": "Vector Algebra & Kinematics in 2D", "subject": "Physics", "class": "Class 11", "desc": "Dot product, cross product, projectile motion, parabolic trajectory", "misc": "Believes horizontal velocity of projectile changes during flight"},
    {"id": "c11_phys_thermo", "name": "Thermodynamics & Heat Engines", "subject": "Physics", "class": "Class 11", "desc": "First and second laws of thermodynamics, Carnot engine efficiency, entropy", "misc": "Believes 100% efficient heat engine is possible in practice"},
    {"id": "c11_chem_quantum", "name": "Structure of Atom & Quantum Numbers", "subject": "Chemistry", "class": "Class 11", "desc": "Bohr model, de Broglie wavelength, Heisenberg uncertainty, s,p,d,f orbitals", "misc": "Believes electrons follow fixed 2D planetary orbits"},
    {"id": "c11_bio_biomolecules", "name": "Biomolecules & Enzyme Kinetics", "subject": "Biology", "class": "Class 11", "desc": "Proteins, carbohydrates, lipids, nucleic acids, enzyme activation energy", "misc": "Believes enzymes are consumed in chemical reactions"},
    
    {"id": "c12_phys_electro", "name": "Electrostatics & Gauss's Law", "subject": "Physics", "class": "Class 12", "desc": "Electric dipole, flux, Gauss theorem, electric potential, capacitors", "misc": "Believes electric field inside a hollow conductor is non-zero"},
    {"id": "c12_phys_optics", "name": "Wave Optics & Interference", "subject": "Physics", "class": "Class 12", "desc": "Huygens principle, Young's double slit experiment, fringe width, diffraction", "misc": "Believes light interference violates conservation of energy"},
    {"id": "c12_chem_kinetics", "name": "Chemical Kinetics & Order of Reaction", "subject": "Chemistry", "class": "Class 12", "desc": "Rate law, zero and first order reactions, Arrhenius equation, catalyst role", "misc": "Believes reaction order must equal stoichiometric coefficients"},
    {"id": "c12_bio_genetics", "name": "Molecular Basis of Inheritance", "subject": "Biology", "class": "Class 12", "desc": "DNA replication, transcription, genetic code, translation, lac operon", "misc": "Believes RNA polymerase reads DNA in 3' to 5' direction"},

    # SOCIAL SCIENCES (HISTORY, GEOGRAPHY, CIVICS, ECONOMICS)
    {"id": "c9_hist_french", "name": "The French Revolution", "subject": "History", "class": "Class 9", "desc": "Three estates, storming of Bastille, Declaration of Rights of Man, Reign of Terror", "misc": "Believes third estate included nobility and clergy"},
    {"id": "c9_geog_india", "name": "India - Size and Location", "subject": "Geography", "class": "Class 9", "desc": "Latitudinal and longitudinal extent, Tropic of Cancer, Standard Meridian 82°30'E", "misc": "Believes Indian standard time varies across states"},
    {"id": "c10_civics_power", "name": "Power Sharing & Federalism", "subject": "Civics", "class": "Class 10", "desc": "Belgian model, Sri Lankan majoritarianism, vertical and horizontal distribution of power", "misc": "Believes federalism means central government holds absolute authority"},
    {"id": "c10_econ_dev", "name": "Development & Per Capita Income", "subject": "Economics", "class": "Class 10", "desc": "GDP, Per Capita Income, Human Development Index (HDI), sustainable development", "misc": "Believes high GDP automatically guarantees high quality of life for all citizens"},
]


def get_ncert_curriculum_graph() -> KnowledgeGraph:
    kg = KnowledgeGraph()
    for item in NCERT_CATALOG:
        c = Concept(
            id=item["id"],
            name=item["name"],
            description=f"{item['class']} {item['subject']}: {item['desc']}",
            domain=item["subject"],
            grade_level=item["class"],
            prerequisite_ids=[],
            misconceptions=[
                Misconception(
                    id=f"m_{item['id']}",
                    description=item["misc"],
                    typical_trigger="Core Concept Explanation",
                    correct_conception=item["desc"]
                )
            ]
        )
        kg.add_concept(c)
    return kg
