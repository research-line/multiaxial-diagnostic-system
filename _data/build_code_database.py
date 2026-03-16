#!/usr/bin/env python3
"""
==========================================================================
Build Diagnostic Code Database (SQLite)
Multiaxial Diagnostic Expert System
==========================================================================

Creates diagnostic_codes.db with:
- ICD-11 codes (Chapter 06 Psychiatric + common medical)
- DSM-5-TR codes with ICD-10-CM mapping
- ICF codes (Mental Health Core Sets)
- Cross-mapping DSM-5-TR <-> ICD-11

Architecture: SQLite for offline use, expandable to full ICD-11/ICF/DSM-5.

Run: python build_code_database.py
==========================================================================
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostic_codes.db")


# ===================================================================
# SCHEMA
# ===================================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS icd11 (
    code TEXT PRIMARY KEY,
    title_de TEXT NOT NULL,
    title_en TEXT NOT NULL,
    chapter TEXT,
    block TEXT
);

CREATE TABLE IF NOT EXISTS dsm5 (
    icd10cm_code TEXT PRIMARY KEY,
    title_de TEXT NOT NULL,
    title_en TEXT NOT NULL,
    dsm5_category TEXT
);

CREATE TABLE IF NOT EXISTS icf (
    code TEXT PRIMARY KEY,
    title_de TEXT NOT NULL,
    title_en TEXT NOT NULL,
    component TEXT
);

CREATE TABLE IF NOT EXISTS code_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_system TEXT NOT NULL,
    source_code TEXT NOT NULL,
    target_system TEXT NOT NULL,
    target_code TEXT NOT NULL,
    mapping_quality TEXT DEFAULT 'equivalent'
);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_icd11_title_de ON icd11(title_de);
CREATE INDEX IF NOT EXISTS idx_icd11_title_en ON icd11(title_en);
CREATE INDEX IF NOT EXISTS idx_icd11_chapter ON icd11(chapter);
CREATE INDEX IF NOT EXISTS idx_dsm5_title_de ON dsm5(title_de);
CREATE INDEX IF NOT EXISTS idx_dsm5_title_en ON dsm5(title_en);
CREATE INDEX IF NOT EXISTS idx_dsm5_category ON dsm5(dsm5_category);
CREATE INDEX IF NOT EXISTS idx_icf_title_de ON icf(title_de);
CREATE INDEX IF NOT EXISTS idx_icf_component ON icf(component);
CREATE INDEX IF NOT EXISTS idx_mapping_source ON code_mapping(source_system, source_code);
CREATE INDEX IF NOT EXISTS idx_mapping_target ON code_mapping(target_system, target_code);
"""


# ===================================================================
# ICD-11 DATA: Chapter 06 - Mental, Behavioural, Neurodevelopmental
# ===================================================================

ICD11_PSYCHIATRIC = [
    # --- Neurodevelopmental Disorders (6A00-6A0Z) ---
    ("6A00", "Entwicklungsstoerungen der Intelligenz", "Disorders of intellectual development", "06", "Neurodevelopmental"),
    ("6A00.0", "Intelligenzminderung, leicht", "Disorder of intellectual development, mild", "06", "Neurodevelopmental"),
    ("6A00.1", "Intelligenzminderung, mittelgradig", "Disorder of intellectual development, moderate", "06", "Neurodevelopmental"),
    ("6A00.2", "Intelligenzminderung, schwer", "Disorder of intellectual development, severe", "06", "Neurodevelopmental"),
    ("6A00.3", "Intelligenzminderung, schwerst", "Disorder of intellectual development, profound", "06", "Neurodevelopmental"),
    ("6A01", "Entwicklungsstoerungen des Sprechens oder der Sprache", "Developmental speech or language disorders", "06", "Neurodevelopmental"),
    ("6A02", "Autismus-Spektrum-Stoerung", "Autism spectrum disorder", "06", "Neurodevelopmental"),
    ("6A03", "Entwicklungsstoerung des Lernens", "Developmental learning disorder", "06", "Neurodevelopmental"),
    ("6A04", "Entwicklungsstoerung der motorischen Koordination", "Developmental motor coordination disorder", "06", "Neurodevelopmental"),
    ("6A05", "Aufmerksamkeitsdefizit-/Hyperaktivitaetsstoerung", "Attention deficit hyperactivity disorder", "06", "Neurodevelopmental"),
    ("6A05.0", "ADHS, vorwiegend unaufmerksam", "ADHD, predominantly inattentive presentation", "06", "Neurodevelopmental"),
    ("6A05.1", "ADHS, vorwiegend hyperaktiv-impulsiv", "ADHD, predominantly hyperactive-impulsive presentation", "06", "Neurodevelopmental"),
    ("6A05.2", "ADHS, kombiniert", "ADHD, combined presentation", "06", "Neurodevelopmental"),
    ("6A06", "Stereotype Bewegungsstoerung", "Stereotyped movement disorder", "06", "Neurodevelopmental"),

    # --- Schizophrenia Spectrum (6A20-6A2Z) ---
    ("6A20", "Schizophrenie", "Schizophrenia", "06", "Schizophrenia spectrum"),
    ("6A20.0", "Schizophrenie, Erstepisode", "Schizophrenia, first episode", "06", "Schizophrenia spectrum"),
    ("6A20.1", "Schizophrenie, multiple Episoden", "Schizophrenia, multiple episodes", "06", "Schizophrenia spectrum"),
    ("6A20.2", "Schizophrenie, kontinuierlich", "Schizophrenia, continuous", "06", "Schizophrenia spectrum"),
    ("6A21", "Schizoaffektive Stoerung", "Schizoaffective disorder", "06", "Schizophrenia spectrum"),
    ("6A22", "Schizotype Stoerung", "Schizotypal disorder", "06", "Schizophrenia spectrum"),
    ("6A23", "Akute voruebergehende psychotische Stoerung", "Acute and transient psychotic disorder", "06", "Schizophrenia spectrum"),
    ("6A24", "Wahnhafte Stoerung", "Delusional disorder", "06", "Schizophrenia spectrum"),

    # --- Catatonia (6A40) ---
    ("6A40", "Katatonie in Verbindung mit einer anderen psychischen Stoerung", "Catatonia associated with another mental disorder", "06", "Catatonia"),
    ("6A41", "Katatonie durch psychoaktive Substanzen", "Catatonia induced by substances or medications", "06", "Catatonia"),

    # --- Mood Disorders (6A60-6A8Z) ---
    ("6A60", "Bipolare Stoerung Typ I", "Bipolar type I disorder", "06", "Mood disorders"),
    ("6A60.0", "Bipolar I, aktuelle Episode manisch, ohne psychotische Symptome", "Bipolar I, current episode manic, without psychotic symptoms", "06", "Mood disorders"),
    ("6A60.1", "Bipolar I, aktuelle Episode manisch, mit psychotischen Symptomen", "Bipolar I, current episode manic, with psychotic symptoms", "06", "Mood disorders"),
    ("6A60.2", "Bipolar I, aktuelle Episode depressiv, leicht", "Bipolar I, current episode depressive, mild", "06", "Mood disorders"),
    ("6A60.3", "Bipolar I, aktuelle Episode depressiv, mittelgradig", "Bipolar I, current episode depressive, moderate", "06", "Mood disorders"),
    ("6A60.5", "Bipolar I, aktuelle Episode depressiv, schwer", "Bipolar I, current episode depressive, severe", "06", "Mood disorders"),
    ("6A60.7", "Bipolar I, aktuelle Episode gemischt", "Bipolar I, current episode mixed", "06", "Mood disorders"),
    ("6A61", "Bipolare Stoerung Typ II", "Bipolar type II disorder", "06", "Mood disorders"),
    ("6A62", "Zyklothyme Stoerung", "Cyclothymic disorder", "06", "Mood disorders"),
    ("6A70", "Depressive Episode", "Single episode depressive disorder", "06", "Mood disorders"),
    ("6A70.0", "Depressive Episode, leicht", "Single episode depressive disorder, mild", "06", "Mood disorders"),
    ("6A70.1", "Depressive Episode, mittelgradig, ohne psychotische Symptome", "Single episode depressive disorder, moderate, without psychotic symptoms", "06", "Mood disorders"),
    ("6A70.2", "Depressive Episode, mittelgradig, mit psychotischen Symptomen", "Single episode depressive disorder, moderate, with psychotic symptoms", "06", "Mood disorders"),
    ("6A70.3", "Depressive Episode, schwer, ohne psychotische Symptome", "Single episode depressive disorder, severe, without psychotic symptoms", "06", "Mood disorders"),
    ("6A70.4", "Depressive Episode, schwer, mit psychotischen Symptomen", "Single episode depressive disorder, severe, with psychotic symptoms", "06", "Mood disorders"),
    ("6A71", "Rezidivierende depressive Stoerung", "Recurrent depressive disorder", "06", "Mood disorders"),
    ("6A71.0", "Rezidivierende depressive Stoerung, gegenwaertige Episode leicht", "Recurrent depressive disorder, current episode mild", "06", "Mood disorders"),
    ("6A71.1", "Rezidivierende depressive Stoerung, gegenwaertige Episode mittelgradig", "Recurrent depressive disorder, current episode moderate", "06", "Mood disorders"),
    ("6A71.3", "Rezidivierende depressive Stoerung, gegenwaertige Episode schwer", "Recurrent depressive disorder, current episode severe", "06", "Mood disorders"),
    ("6A71.4", "Rezidivierende depressive Stoerung, gegenwaertige Episode schwer, mit Psychose", "Recurrent depressive disorder, current episode severe with psychotic symptoms", "06", "Mood disorders"),
    ("6A72", "Dysthyme Stoerung", "Dysthymic disorder", "06", "Mood disorders"),
    ("6A73", "Gemischte depressive und Angststoerung", "Mixed depressive and anxiety disorder", "06", "Mood disorders"),

    # --- Anxiety and Fear-Related Disorders (6B00-6B0Z) ---
    ("6B00", "Generalisierte Angststoerung", "Generalised anxiety disorder", "06", "Anxiety"),
    ("6B01", "Panikstoerung", "Panic disorder", "06", "Anxiety"),
    ("6B02", "Agoraphobie", "Agoraphobia", "06", "Anxiety"),
    ("6B03", "Spezifische Phobie", "Specific phobia", "06", "Anxiety"),
    ("6B04", "Soziale Angststoerung", "Social anxiety disorder", "06", "Anxiety"),
    ("6B05", "Trennungsangststoerung", "Separation anxiety disorder", "06", "Anxiety"),
    ("6B06", "Selektiver Mutismus", "Selective mutism", "06", "Anxiety"),

    # --- OCD and Related (6B20-6B2Z) ---
    ("6B20", "Zwangsstoerung", "Obsessive-compulsive disorder", "06", "OCD"),
    ("6B21", "Koerperdysmorphe Stoerung", "Body dysmorphic disorder", "06", "OCD"),
    ("6B22", "Olfaktorische Referenzstoerung", "Olfactory reference disorder", "06", "OCD"),
    ("6B23", "Hypochondrie (Krankheitsangst)", "Hypochondriasis (health anxiety)", "06", "OCD"),
    ("6B24", "Pathologisches Horten", "Hoarding disorder", "06", "OCD"),
    ("6B25", "Koerperbezogene repetitive Verhaltensstoerungen", "Body-focused repetitive behaviour disorders", "06", "OCD"),
    ("6B25.0", "Trichotillomanie", "Trichotillomania", "06", "OCD"),
    ("6B25.1", "Dermatillomanie (Skin Picking)", "Excoriation disorder", "06", "OCD"),

    # --- Stress-Related Disorders (6B40-6B4Z) ---
    ("6B40", "Posttraumatische Belastungsstoerung", "Post traumatic stress disorder", "06", "Stress-related"),
    ("6B41", "Komplexe Posttraumatische Belastungsstoerung", "Complex post traumatic stress disorder", "06", "Stress-related"),
    ("6B42", "Anhaltende Trauerstoerung", "Prolonged grief disorder", "06", "Stress-related"),
    ("6B43", "Anpassungsstoerung", "Adjustment disorder", "06", "Stress-related"),
    ("6B44", "Reaktive Bindungsstoerung", "Reactive attachment disorder", "06", "Stress-related"),
    ("6B45", "Enthemmte Bindungsstoerung", "Disinhibited social engagement disorder", "06", "Stress-related"),

    # --- Dissociative Disorders (6B60-6B6Z) ---
    ("6B60", "Dissoziative neurologische Symptomstoerung", "Dissociative neurological symptom disorder", "06", "Dissociative"),
    ("6B61", "Dissoziative Amnesie", "Dissociative amnesia", "06", "Dissociative"),
    ("6B64", "Dissoziative Identitaetsstoerung", "Dissociative identity disorder", "06", "Dissociative"),
    ("6B65", "Partielle dissoziative Identitaetsstoerung", "Partial dissociative identity disorder", "06", "Dissociative"),
    ("6B66", "Depersonalisations-/Derealisationsstoerung", "Depersonalisation-derealisation disorder", "06", "Dissociative"),

    # --- Feeding and Eating Disorders (6B80-6B8Z) ---
    ("6B80", "Anorexia nervosa", "Anorexia nervosa", "06", "Eating disorders"),
    ("6B80.0", "Anorexia nervosa, restriktiver Typ", "Anorexia nervosa, restricting pattern", "06", "Eating disorders"),
    ("6B80.1", "Anorexia nervosa, Binge-Purge-Typ", "Anorexia nervosa, binge-purge pattern", "06", "Eating disorders"),
    ("6B81", "Bulimia nervosa", "Bulimia nervosa", "06", "Eating disorders"),
    ("6B82", "Binge-Eating-Stoerung", "Binge eating disorder", "06", "Eating disorders"),
    ("6B83", "Vermeidend-restriktive Nahrungsaufnahmestoerung (ARFID)", "Avoidant-restrictive food intake disorder", "06", "Eating disorders"),
    ("6B84", "Pica", "Pica", "06", "Eating disorders"),

    # --- Disorders due to Substance Use (6C40-6C4Z) ---
    ("6C40", "Stoerungen durch Alkoholgebrauch", "Disorders due to use of alcohol", "06", "Substance use"),
    ("6C40.0", "Schaedlicher Alkoholgebrauch, Episode", "Episode of harmful use of alcohol", "06", "Substance use"),
    ("6C40.1", "Schaedliches Muster des Alkoholgebrauchs", "Harmful pattern of use of alcohol", "06", "Substance use"),
    ("6C40.2", "Alkoholabhaengigkeit", "Alcohol dependence", "06", "Substance use"),
    ("6C40.3", "Alkoholintoxikation", "Alcohol intoxication", "06", "Substance use"),
    ("6C40.4", "Alkoholentzugssyndrom", "Alcohol withdrawal", "06", "Substance use"),
    ("6C41", "Stoerungen durch Cannabisgebrauch", "Disorders due to use of cannabis", "06", "Substance use"),
    ("6C41.2", "Cannabisabhaengigkeit", "Cannabis dependence", "06", "Substance use"),
    ("6C43", "Stoerungen durch Opioidgebrauch", "Disorders due to use of opioids", "06", "Substance use"),
    ("6C43.2", "Opioidabhaengigkeit", "Opioid dependence", "06", "Substance use"),
    ("6C44", "Stoerungen durch Sedativa/Hypnotika", "Disorders due to use of sedatives, hypnotics or anxiolytics", "06", "Substance use"),
    ("6C44.2", "Sedativa-/Hypnotikaabhaengigkeit", "Sedative, hypnotic or anxiolytic dependence", "06", "Substance use"),
    ("6C45", "Stoerungen durch Kokaingebrauch", "Disorders due to use of cocaine", "06", "Substance use"),
    ("6C45.2", "Kokainabhaengigkeit", "Cocaine dependence", "06", "Substance use"),
    ("6C46", "Stoerungen durch Stimulanzien (Amphetamine)", "Disorders due to use of stimulants including amphetamines", "06", "Substance use"),
    ("6C46.2", "Stimulanzienabhaengigkeit", "Stimulant dependence", "06", "Substance use"),
    ("6C49", "Stoerungen durch Halluzinogengebrauch", "Disorders due to use of hallucinogens", "06", "Substance use"),
    ("6C4A", "Stoerungen durch Nikotingebrauch", "Disorders due to use of nicotine", "06", "Substance use"),
    ("6C4A.2", "Nikotinabhaengigkeit", "Nicotine dependence", "06", "Substance use"),

    # --- Gambling Disorder ---
    ("6C50", "Stoerung durch Gluecksspiel", "Gambling disorder", "06", "Impulse control"),

    # --- Impulse Control Disorders (6C70-6C7Z) ---
    ("6C70", "Pyromanie", "Pyromania", "06", "Impulse control"),
    ("6C71", "Kleptomanie", "Kleptomania", "06", "Impulse control"),
    ("6C72", "Intermittierende explosible Stoerung", "Intermittent explosive disorder", "06", "Impulse control"),
    ("6C73", "Gaming-Stoerung (Computerspielsucht)", "Gaming disorder", "06", "Impulse control"),

    # --- Disruptive Behaviour (6C90-6C9Z) ---
    ("6C90", "Stoerung des Sozialverhaltens mit oppositionellem Verhalten", "Oppositional defiant disorder", "06", "Disruptive behaviour"),
    ("6C91", "Stoerung des Sozialverhaltens, dissozial", "Conduct-dissocial disorder", "06", "Disruptive behaviour"),

    # --- Personality Disorders (6D10-6D1Z) -- ICD-11 dimensional ---
    ("6D10", "Persoenlichkeitsstoerung", "Personality disorder", "06", "Personality"),
    ("6D10.0", "Persoenlichkeitsstoerung, leicht", "Personality disorder, mild", "06", "Personality"),
    ("6D10.1", "Persoenlichkeitsstoerung, mittelgradig", "Personality disorder, moderate", "06", "Personality"),
    ("6D10.2", "Persoenlichkeitsstoerung, schwer", "Personality disorder, severe", "06", "Personality"),
    ("6D11", "Persoenlichkeitsschwierigkeit", "Personality difficulty", "06", "Personality"),

    # --- Paraphilic Disorders (6D30-6D3Z) ---
    ("6D30", "Exhibitionistische Stoerung", "Exhibitionistic disorder", "06", "Paraphilic"),
    ("6D31", "Voyeuristische Stoerung", "Voyeuristic disorder", "06", "Paraphilic"),
    ("6D33", "Sexueller Sadismus (koerziv)", "Coercive sexual sadism disorder", "06", "Paraphilic"),

    # --- Factitious Disorders (6D50-6D5Z) ---
    ("6D50", "Artifizielle Stoerung, selbstbezogen", "Factitious disorder imposed on self", "06", "Factitious"),
    ("6D51", "Artifizielle Stoerung, fremdbezogen", "Factitious disorder imposed on another", "06", "Factitious"),

    # --- Neurocognitive Disorders (6D70-6D8Z) ---
    ("6D70", "Delir", "Delirium", "06", "Neurocognitive"),
    ("6D71", "Leichte neurokognitive Stoerung", "Mild neurocognitive disorder", "06", "Neurocognitive"),
    ("6D72", "Amnestische Stoerung", "Amnestic disorder", "06", "Neurocognitive"),
    ("6D80", "Demenz bei Alzheimer-Krankheit", "Dementia due to Alzheimer disease", "06", "Neurocognitive"),
    ("6D81", "Vaskulaere Demenz", "Dementia due to cerebrovascular disease", "06", "Neurocognitive"),
    ("6D82", "Demenz mit Lewy-Koerperchen", "Dementia due to Lewy body disease", "06", "Neurocognitive"),
    ("6D83", "Frontotemporale Demenz", "Frontotemporal dementia", "06", "Neurocognitive"),
    ("6D84", "Substanzinduzierte Demenz", "Dementia due to psychoactive substances", "06", "Neurocognitive"),

    # --- Secondary Mental Syndromes (6E60-6E6Z) ---
    ("6E60", "Sekundaeres psychotisches Syndrom", "Secondary psychotic syndrome", "06", "Secondary"),
    ("6E61", "Sekundaeres Stimmungssyndrom", "Secondary mood syndrome", "06", "Secondary"),
    ("6E62", "Sekundaeres Angstsyndrom", "Secondary anxiety syndrome", "06", "Secondary"),
    ("6E63", "Sekundaeres Zwangssyndrom", "Secondary obsessive-compulsive syndrome", "06", "Secondary"),
    ("6E64", "Sekundaeres dissoziatives Syndrom", "Secondary dissociative syndrome", "06", "Secondary"),
    ("6E65", "Sekundaeres Impulskontrollsyndrom", "Secondary impulse control syndrome", "06", "Secondary"),
    ("6E68", "Sekundaeres neurokognitives Syndrom", "Secondary neurocognitive syndrome", "06", "Secondary"),
]

# ===================================================================
# ICD-11: Sleep-Wake Disorders (Chapter 07) - psychiatrically relevant
# ===================================================================

ICD11_SLEEP = [
    ("7A00", "Insomnie", "Insomnia disorder", "07", "Sleep-wake"),
    ("7A01", "Hypersomnolenzstoerung", "Hypersomnolence disorder", "07", "Sleep-wake"),
    ("7A20", "Narkolepsie", "Narcolepsy", "07", "Sleep-wake"),
    ("7A40", "Obstruktive Schlafapnoe", "Obstructive sleep apnoea", "07", "Sleep-wake"),
    ("7A60", "Restless-Legs-Syndrom", "Restless legs syndrome", "07", "Sleep-wake"),
    ("7B00", "Alptraumstoerung", "Nightmare disorder", "07", "Sleep-wake"),
    ("7B01", "Pavor nocturnus", "Sleep terrors", "07", "Sleep-wake"),
    ("7B02", "Schlafwandeln (Somnambulismus)", "Sleepwalking", "07", "Sleep-wake"),
]

# ===================================================================
# ICD-11: Gender Incongruence (Chapter 17)
# ===================================================================

ICD11_GENDER = [
    ("HA60", "Geschlechtsinkongruenz des Jugend- oder Erwachsenenalters", "Gender incongruence of adolescence or adulthood", "17", "Gender incongruence"),
    ("HA61", "Geschlechtsinkongruenz des Kindesalters", "Gender incongruence of childhood", "17", "Gender incongruence"),
]

# ===================================================================
# ICD-11: Common Medical Diagnoses (psychiatrically relevant)
# ===================================================================

ICD11_MEDICAL = [
    # Endocrine
    ("5A00", "Hypothyreose", "Hypothyroidism", "05", "Endocrine"),
    ("5A01", "Hyperthyreose", "Hyperthyroidism", "05", "Endocrine"),
    ("5A02", "Thyreoiditis", "Thyroiditis", "05", "Endocrine"),
    ("5A10", "Diabetes mellitus Typ 1", "Type 1 diabetes mellitus", "05", "Endocrine"),
    ("5A11", "Diabetes mellitus Typ 2", "Type 2 diabetes mellitus", "05", "Endocrine"),
    ("5A70", "Cushing-Syndrom", "Cushing syndrome", "05", "Endocrine"),
    ("5A74", "Nebennierenrindeninsuffizienz (Morbus Addison)", "Adrenocortical insufficiency", "05", "Endocrine"),

    # Neurological
    ("8A00", "Epilepsie", "Epilepsy", "08", "Neurological"),
    ("8A00.0", "Fokale Epilepsie", "Focal epilepsy", "08", "Neurological"),
    ("8A00.1", "Generalisierte Epilepsie", "Generalised epilepsy", "08", "Neurological"),
    ("8A05.00", "Tourette-Syndrom", "Tourette syndrome", "08", "Neurological"),
    ("8A20", "Parkinson-Krankheit", "Parkinson disease", "08", "Neurological"),
    ("8A40", "Multiple Sklerose", "Multiple sclerosis", "08", "Neurological"),
    ("8A43", "Myasthenia gravis", "Myasthenia gravis", "08", "Neurological"),
    ("8B00", "Schlaganfall (ischaemisch)", "Ischaemic stroke", "08", "Neurological"),
    ("8B01", "Schlaganfall (haemorrhagisch)", "Haemorrhagic stroke", "08", "Neurological"),
    ("8B20", "Migraene", "Migraine", "08", "Neurological"),
    ("8B22", "Spannungskopfschmerz", "Tension-type headache", "08", "Neurological"),
    ("NA07", "Schaedel-Hirn-Trauma", "Traumatic brain injury", "22", "Neurological"),

    # Cardiovascular
    ("BA00", "Essentielle Hypertonie", "Essential hypertension", "11", "Cardiovascular"),
    ("BA80", "Herzinsuffizienz", "Heart failure", "11", "Cardiovascular"),
    ("BA41", "Koronare Herzkrankheit", "Coronary artery disease", "11", "Cardiovascular"),

    # Chronic Pain
    ("MG30", "Chronischer Schmerz", "Chronic pain", "21", "Pain"),
    ("MG30.0", "Chronischer primaerer Schmerz", "Chronic primary pain", "21", "Pain"),
    ("MG30.1", "Chronischer Krebsschmerz", "Chronic cancer-related pain", "21", "Pain"),
    ("MG30.3", "Chronischer neuropathischer Schmerz", "Chronic neuropathic pain", "21", "Pain"),
    ("FB54", "Fibromyalgie", "Fibromyalgia", "15", "Pain"),

    # Autoimmune
    ("4A40", "Systemischer Lupus erythematodes", "Systemic lupus erythematosus", "04", "Autoimmune"),
    ("FA20", "Rheumatoide Arthritis", "Rheumatoid arthritis", "15", "Autoimmune"),

    # Infectious (psychiatrically relevant)
    ("1C60", "HIV-Krankheit", "HIV disease", "01", "Infectious"),
    ("1E50", "Hepatitis C", "Hepatitis C", "01", "Infectious"),

    # Other
    ("DA94", "Reizdarmsyndrom", "Irritable bowel syndrome", "13", "Gastrointestinal"),
    ("CA20", "Asthma bronchiale", "Asthma", "12", "Respiratory"),
]


# ===================================================================
# DSM-5-TR DATA (ICD-10-CM Codes)
# ===================================================================

DSM5_DATA = [
    # --- Neurodevelopmental ---
    ("F70", "Leichte Intelligenzminderung", "Mild intellectual disability", "Neurodevelopmental"),
    ("F71", "Mittelgradige Intelligenzminderung", "Moderate intellectual disability", "Neurodevelopmental"),
    ("F72", "Schwere Intelligenzminderung", "Severe intellectual disability", "Neurodevelopmental"),
    ("F84.0", "Autismus-Spektrum-Stoerung", "Autism spectrum disorder", "Neurodevelopmental"),
    ("F80.9", "Sprachstoerung", "Language disorder", "Neurodevelopmental"),
    ("F80.0", "Artikulationsstoerung", "Speech sound disorder", "Neurodevelopmental"),
    ("F80.81", "Redeflussstoerung (Stottern)", "Childhood-onset fluency disorder (stuttering)", "Neurodevelopmental"),
    ("F81.0", "Lesestoerung (Dyslexie)", "Specific learning disorder with impairment in reading", "Neurodevelopmental"),
    ("F81.81", "Rechenstoerung (Dyskalkulie)", "Specific learning disorder with impairment in mathematics", "Neurodevelopmental"),
    ("F81.2", "Schreibstoerung (Dysgraphie)", "Specific learning disorder with impairment in written expression", "Neurodevelopmental"),
    ("F82", "Entwicklungsbezogene Koordinationsstoerung", "Developmental coordination disorder", "Neurodevelopmental"),
    ("F90.0", "ADHS, vorwiegend unaufmerksam", "ADHD, predominantly inattentive presentation", "Neurodevelopmental"),
    ("F90.1", "ADHS, vorwiegend hyperaktiv-impulsiv", "ADHD, predominantly hyperactive-impulsive presentation", "Neurodevelopmental"),
    ("F90.2", "ADHS, kombiniert", "ADHD, combined presentation", "Neurodevelopmental"),
    ("F95.0", "Voruebergehende Ticstoerung", "Provisional tic disorder", "Neurodevelopmental"),
    ("F95.1", "Chronische motorische oder vokale Ticstoerung", "Persistent motor or vocal tic disorder", "Neurodevelopmental"),
    ("F95.2", "Tourette-Stoerung", "Tourette's disorder", "Neurodevelopmental"),

    # --- Schizophrenia Spectrum ---
    ("F20.9", "Schizophrenie", "Schizophrenia", "Schizophrenia spectrum"),
    ("F25.0", "Schizoaffektive Stoerung, bipolarer Typ", "Schizoaffective disorder, bipolar type", "Schizophrenia spectrum"),
    ("F25.1", "Schizoaffektive Stoerung, depressiver Typ", "Schizoaffective disorder, depressive type", "Schizophrenia spectrum"),
    ("F21", "Schizotype Persoenlichkeitsstoerung", "Schizotypal personality disorder", "Schizophrenia spectrum"),
    ("F22", "Wahnhafte Stoerung", "Delusional disorder", "Schizophrenia spectrum"),
    ("F23", "Kurze psychotische Stoerung", "Brief psychotic disorder", "Schizophrenia spectrum"),

    # --- Bipolar and Related ---
    ("F31.0", "Bipolar I, aktuelle Episode hypomanisch", "Bipolar I, current episode hypomanic", "Bipolar"),
    ("F31.11", "Bipolar I, aktuelle Episode manisch, leicht", "Bipolar I, current episode manic, mild", "Bipolar"),
    ("F31.12", "Bipolar I, aktuelle Episode manisch, mittelgradig", "Bipolar I, current episode manic, moderate", "Bipolar"),
    ("F31.13", "Bipolar I, aktuelle Episode manisch, schwer", "Bipolar I, current episode manic, severe", "Bipolar"),
    ("F31.2", "Bipolar I, aktuelle Episode manisch mit Psychose", "Bipolar I, current episode manic with psychotic features", "Bipolar"),
    ("F31.31", "Bipolar I, aktuelle Episode depressiv, leicht", "Bipolar I, current episode depressed, mild", "Bipolar"),
    ("F31.32", "Bipolar I, aktuelle Episode depressiv, mittelgradig", "Bipolar I, current episode depressed, moderate", "Bipolar"),
    ("F31.4", "Bipolar I, aktuelle Episode depressiv, schwer", "Bipolar I, current episode depressed, severe", "Bipolar"),
    ("F31.5", "Bipolar I, aktuelle Episode depressiv mit Psychose", "Bipolar I, current episode depressed with psychotic features", "Bipolar"),
    ("F31.81", "Bipolare Stoerung Typ II", "Bipolar II disorder", "Bipolar"),
    ("F34.0", "Zyklothyme Stoerung", "Cyclothymic disorder", "Bipolar"),

    # --- Depressive Disorders ---
    ("F32.0", "Depressive Episode, leicht", "Major depressive disorder, single episode, mild", "Depressive"),
    ("F32.1", "Depressive Episode, mittelgradig", "Major depressive disorder, single episode, moderate", "Depressive"),
    ("F32.2", "Depressive Episode, schwer", "Major depressive disorder, single episode, severe", "Depressive"),
    ("F32.3", "Depressive Episode, schwer mit psychotischen Merkmalen", "Major depressive disorder, single episode, with psychotic features", "Depressive"),
    ("F33.0", "Rezidivierende depressive Stoerung, leicht", "Major depressive disorder, recurrent, mild", "Depressive"),
    ("F33.1", "Rezidivierende depressive Stoerung, mittelgradig", "Major depressive disorder, recurrent, moderate", "Depressive"),
    ("F33.2", "Rezidivierende depressive Stoerung, schwer", "Major depressive disorder, recurrent, severe", "Depressive"),
    ("F33.3", "Rezidivierende depressive Stoerung, schwer mit Psychose", "Major depressive disorder, recurrent, with psychotic features", "Depressive"),
    ("F34.1", "Persistierende depressive Stoerung (Dysthymie)", "Persistent depressive disorder (dysthymia)", "Depressive"),
    ("F32.81", "Praemenstruelle dysphorische Stoerung", "Premenstrual dysphoric disorder", "Depressive"),
    ("N94.3", "Praemenstruelles Syndrom", "Premenstrual tension syndrome", "Depressive"),

    # --- Anxiety Disorders ---
    ("F41.1", "Generalisierte Angststoerung", "Generalized anxiety disorder", "Anxiety"),
    ("F41.0", "Panikstoerung", "Panic disorder", "Anxiety"),
    ("F40.00", "Agoraphobie", "Agoraphobia", "Anxiety"),
    ("F40.10", "Soziale Angststoerung (Soziale Phobie)", "Social anxiety disorder", "Anxiety"),
    ("F40.218", "Spezifische Phobie, Tier-Typ", "Specific phobia, animal type", "Anxiety"),
    ("F40.228", "Spezifische Phobie, Naturereignis-Typ", "Specific phobia, natural environment type", "Anxiety"),
    ("F40.230", "Spezifische Phobie, Blut-Typ", "Specific phobia, blood-injection-injury type", "Anxiety"),
    ("F40.248", "Spezifische Phobie, situativer Typ", "Specific phobia, situational type", "Anxiety"),
    ("F93.0", "Trennungsangststoerung", "Separation anxiety disorder", "Anxiety"),
    ("F94.0", "Selektiver Mutismus", "Selective mutism", "Anxiety"),

    # --- OCD and Related ---
    ("F42.2", "Zwangsstoerung", "Obsessive-compulsive disorder", "OCD"),
    ("F42.3", "Horten", "Hoarding disorder", "OCD"),
    ("F45.22", "Koerperdysmorphe Stoerung", "Body dysmorphic disorder", "OCD"),
    ("F63.3", "Trichotillomanie", "Trichotillomania (hair-pulling disorder)", "OCD"),
    ("L98.1", "Dermatillomanie (Skin Picking)", "Excoriation (skin-picking) disorder", "OCD"),

    # --- Trauma and Stressor-Related ---
    ("F43.10", "Posttraumatische Belastungsstoerung", "Posttraumatic stress disorder", "Trauma"),
    ("F43.0", "Akute Belastungsreaktion", "Acute stress disorder", "Trauma"),
    ("F43.21", "Anpassungsstoerung mit depressiver Verstimmung", "Adjustment disorder with depressed mood", "Trauma"),
    ("F43.22", "Anpassungsstoerung mit Angst", "Adjustment disorder with anxiety", "Trauma"),
    ("F43.23", "Anpassungsstoerung mit Angst und depressiver Verstimmung gemischt", "Adjustment disorder with mixed anxiety and depressed mood", "Trauma"),
    ("F43.24", "Anpassungsstoerung mit Stoerung des Sozialverhaltens", "Adjustment disorder with disturbance of conduct", "Trauma"),
    ("F43.25", "Anpassungsstoerung mit gemischter Stoerung", "Adjustment disorder with mixed disturbance", "Trauma"),
    ("F94.1", "Reaktive Bindungsstoerung", "Reactive attachment disorder", "Trauma"),
    ("F94.2", "Enthemmte Bindungsstoerung", "Disinhibited social engagement disorder", "Trauma"),

    # --- Dissociative Disorders ---
    ("F44.81", "Dissoziative Identitaetsstoerung", "Dissociative identity disorder", "Dissociative"),
    ("F44.0", "Dissoziative Amnesie", "Dissociative amnesia", "Dissociative"),
    ("F44.1", "Dissoziative Fugue", "Dissociative amnesia with dissociative fugue", "Dissociative"),
    ("F48.1", "Depersonalisations-/Derealisationsstoerung", "Depersonalization/derealization disorder", "Dissociative"),

    # --- Somatic Symptom and Related ---
    ("F45.1", "Somatische Belastungsstoerung", "Somatic symptom disorder", "Somatic"),
    ("F45.21", "Krankheitsangststoerung", "Illness anxiety disorder", "Somatic"),
    ("F44.4", "Konversionsstoerung (Funktionelle neurologische Symptomstoerung)", "Conversion disorder (functional neurological symptom disorder)", "Somatic"),
    ("F68.10", "Artifizielle Stoerung", "Factitious disorder imposed on self", "Somatic"),

    # --- Feeding and Eating ---
    ("F50.01", "Anorexia nervosa, restriktiver Typ", "Anorexia nervosa, restricting type", "Eating"),
    ("F50.02", "Anorexia nervosa, Binge-Purge-Typ", "Anorexia nervosa, binge-eating/purging type", "Eating"),
    ("F50.2", "Bulimia nervosa", "Bulimia nervosa", "Eating"),
    ("F50.81", "Binge-Eating-Stoerung", "Binge eating disorder", "Eating"),
    ("F50.82", "Vermeidend-restriktive Nahrungsaufnahmestoerung (ARFID)", "Avoidant/restrictive food intake disorder", "Eating"),
    ("F50.89", "Andere spezifizierte Fuetterungsstoerung", "Other specified feeding or eating disorder", "Eating"),
    ("F98.3", "Pica im Kindesalter", "Pica in childhood", "Eating"),
    ("F98.21", "Ruminationsstoerung", "Rumination disorder", "Eating"),

    # --- Sleep-Wake ---
    ("G47.00", "Insomnie", "Insomnia disorder", "Sleep-wake"),
    ("G47.10", "Hypersomnolenzstoerung", "Hypersomnolence disorder", "Sleep-wake"),
    ("G47.411", "Narkolepsie Typ 1", "Narcolepsy type 1", "Sleep-wake"),
    ("G47.419", "Narkolepsie Typ 2", "Narcolepsy type 2", "Sleep-wake"),
    ("G47.33", "Obstruktive Schlafapnoe", "Obstructive sleep apnea hypopnea", "Sleep-wake"),

    # --- Substance-Related ---
    ("F10.10", "Alkoholmissbrauch, unkompliziert", "Alcohol use disorder, mild", "Substance use"),
    ("F10.20", "Alkoholabhaengigkeit, unkompliziert", "Alcohol use disorder, moderate/severe", "Substance use"),
    ("F10.239", "Alkoholentzug", "Alcohol withdrawal", "Substance use"),
    ("F12.10", "Cannabismissbrauch", "Cannabis use disorder, mild", "Substance use"),
    ("F12.20", "Cannabisabhaengigkeit", "Cannabis use disorder, moderate/severe", "Substance use"),
    ("F11.10", "Opioidmissbrauch", "Opioid use disorder, mild", "Substance use"),
    ("F11.20", "Opioidabhaengigkeit", "Opioid use disorder, moderate/severe", "Substance use"),
    ("F13.10", "Sedativa-/Hypnotikamissbrauch", "Sedative/hypnotic use disorder, mild", "Substance use"),
    ("F13.20", "Sedativa-/Hypnotikaabhaengigkeit", "Sedative/hypnotic use disorder, moderate/severe", "Substance use"),
    ("F14.10", "Kokainmissbrauch", "Cocaine use disorder, mild", "Substance use"),
    ("F14.20", "Kokainabhaengigkeit", "Cocaine use disorder, moderate/severe", "Substance use"),
    ("F15.10", "Stimulanzienmissbrauch", "Stimulant use disorder, mild", "Substance use"),
    ("F15.20", "Stimulanzienabhaengigkeit", "Stimulant use disorder, moderate/severe", "Substance use"),
    ("F17.200", "Tabakabhaengigkeit", "Tobacco use disorder, moderate/severe", "Substance use"),

    # --- Personality Disorders (DSM-5 categorical) ---
    ("F60.0", "Paranoide Persoenlichkeitsstoerung", "Paranoid personality disorder", "Personality"),
    ("F60.1", "Schizoide Persoenlichkeitsstoerung", "Schizoid personality disorder", "Personality"),
    ("F60.2", "Dissoziale Persoenlichkeitsstoerung (Antisozial)", "Antisocial personality disorder", "Personality"),
    ("F60.3", "Emotional instabile PS, Borderline-Typ", "Borderline personality disorder", "Personality"),
    ("F60.4", "Histrionische Persoenlichkeitsstoerung", "Histrionic personality disorder", "Personality"),
    ("F60.5", "Anankastische (zwanghafte) Persoenlichkeitsstoerung", "Obsessive-compulsive personality disorder", "Personality"),
    ("F60.6", "Aengstliche (vermeidende) Persoenlichkeitsstoerung", "Avoidant personality disorder", "Personality"),
    ("F60.7", "Abhaengige Persoenlichkeitsstoerung", "Dependent personality disorder", "Personality"),
    ("F60.81", "Narzisstische Persoenlichkeitsstoerung", "Narcissistic personality disorder", "Personality"),

    # --- Neurocognitive ---
    ("F05", "Delir", "Delirium", "Neurocognitive"),
    ("G30.9", "Alzheimer-Krankheit", "Alzheimer's disease", "Neurocognitive"),
    ("F01.50", "Vaskulaere Demenz", "Major vascular neurocognitive disorder", "Neurocognitive"),
    ("G31.83", "Lewy-Koerper-Demenz", "Major neurocognitive disorder with Lewy bodies", "Neurocognitive"),
    ("G31.09", "Frontotemporale Demenz", "Major frontotemporal neurocognitive disorder", "Neurocognitive"),

    # --- Impulse Control ---
    ("F63.0", "Pathologisches Gluecksspiel", "Gambling disorder", "Impulse control"),
    ("F63.1", "Pyromanie", "Pyromania", "Impulse control"),
    ("F63.2", "Kleptomanie", "Kleptomania", "Impulse control"),
    ("F63.81", "Intermittierende explosible Stoerung", "Intermittent explosive disorder", "Impulse control"),

    # --- Disruptive Behaviour ---
    ("F91.3", "Stoerung des Sozialverhaltens mit oppositionellem Verhalten", "Oppositional defiant disorder", "Disruptive"),
    ("F91.1", "Stoerung des Sozialverhaltens", "Conduct disorder, childhood-onset type", "Disruptive"),
    ("F91.2", "Stoerung des Sozialverhaltens, Adoleszenz-Typ", "Conduct disorder, adolescent-onset type", "Disruptive"),

    # --- Gender Dysphoria ---
    ("F64.0", "Geschlechtsdysphorie bei Jugendlichen und Erwachsenen", "Gender dysphoria in adolescents and adults", "Gender"),
    ("F64.2", "Geschlechtsdysphorie im Kindesalter", "Gender dysphoria in children", "Gender"),
]


# ===================================================================
# ICF DATA: Mental Health Core Sets
# ===================================================================

ICF_DATA = [
    # --- Body Functions (b) ---
    ("b110", "Bewusstseinsfunktionen", "Consciousness functions", "Body functions"),
    ("b114", "Funktionen der Orientierung", "Orientation functions", "Body functions"),
    ("b117", "Funktionen der Intelligenz", "Intellectual functions", "Body functions"),
    ("b122", "Globale psychosoziale Funktionen", "Global psychosocial functions", "Body functions"),
    ("b126", "Funktionen von Temperament und Persoenlichkeit", "Temperament and personality functions", "Body functions"),
    ("b130", "Funktionen der psychischen Energie und des Antriebs", "Energy and drive functions", "Body functions"),
    ("b134", "Funktionen des Schlafes", "Sleep functions", "Body functions"),
    ("b140", "Funktionen der Aufmerksamkeit", "Attention functions", "Body functions"),
    ("b144", "Funktionen des Gedaechtnisses", "Memory functions", "Body functions"),
    ("b147", "Psychomotorische Funktionen", "Psychomotor functions", "Body functions"),
    ("b152", "Emotionale Funktionen", "Emotional functions", "Body functions"),
    ("b156", "Funktionen der Wahrnehmung", "Perceptual functions", "Body functions"),
    ("b160", "Funktionen des Denkens", "Thought functions", "Body functions"),
    ("b164", "Hoehere kognitive Funktionen", "Higher-level cognitive functions", "Body functions"),
    ("b167", "Kognitiv-sprachliche Funktionen", "Mental functions of language", "Body functions"),
    ("b180", "Die Selbstwahrnehmung betreffende Funktionen", "Experience of self and time functions", "Body functions"),
    ("b280", "Schmerz", "Sensation of pain", "Body functions"),

    # --- Activities & Participation (d) ---
    ("d110", "Zuschauen", "Watching", "Activities"),
    ("d115", "Zuhoeren", "Listening", "Activities"),
    ("d155", "Sich Fertigkeiten aneignen", "Acquiring skills", "Activities"),
    ("d160", "Aufmerksamkeit fokussieren", "Focusing attention", "Activities"),
    ("d163", "Denken", "Thinking", "Activities"),
    ("d166", "Lesen", "Reading", "Activities"),
    ("d170", "Schreiben", "Writing", "Activities"),
    ("d175", "Probleme loesen", "Solving problems", "Activities"),
    ("d177", "Entscheidungen treffen", "Making decisions", "Activities"),
    ("d210", "Eine Einzelaufgabe uebernehmen", "Undertaking a single task", "Activities"),
    ("d220", "Mehrfachaufgaben uebernehmen", "Undertaking multiple tasks", "Activities"),
    ("d230", "Die taegliche Routine durchfuehren", "Carrying out daily routine", "Activities"),
    ("d240", "Mit Stress umgehen", "Handling stress and other psychological demands", "Activities"),
    ("d310", "Kommunizieren als Empfaenger gesprochener Mitteilungen", "Communicating with - receiving - spoken messages", "Activities"),
    ("d330", "Sprechen", "Speaking", "Activities"),
    ("d350", "Konversation", "Conversation", "Activities"),
    ("d410", "Eine elementare Koerperposition wechseln", "Changing basic body position", "Activities"),
    ("d450", "Gehen", "Walking", "Activities"),
    ("d470", "Transportmittel benutzen", "Using transportation", "Activities"),
    ("d510", "Sich waschen", "Washing oneself", "Activities"),
    ("d520", "Seine Koerperteile pflegen", "Caring for body parts", "Activities"),
    ("d530", "Die Toilette benutzen", "Toileting", "Activities"),
    ("d540", "Sich kleiden", "Dressing", "Activities"),
    ("d550", "Essen", "Eating", "Activities"),
    ("d560", "Trinken", "Drinking", "Activities"),
    ("d570", "Auf seine Gesundheit achten", "Looking after one's health", "Activities"),
    ("d620", "Waren und Dienstleistungen des taeglichen Bedarfs beschaffen", "Acquisition of goods and services", "Activities"),
    ("d630", "Mahlzeiten vorbereiten", "Preparing meals", "Activities"),
    ("d640", "Hausarbeiten erledigen", "Doing housework", "Activities"),
    ("d710", "Elementare interpersonelle Aktivitaeten", "Basic interpersonal interactions", "Activities"),
    ("d720", "Komplexe interpersonelle Interaktionen", "Complex interpersonal interactions", "Activities"),
    ("d730", "Mit Fremden umgehen", "Relating with strangers", "Activities"),
    ("d740", "Formelle Beziehungen", "Formal relationships", "Activities"),
    ("d750", "Informelle soziale Beziehungen", "Informal social relationships", "Activities"),
    ("d760", "Familienbeziehungen", "Family relationships", "Activities"),
    ("d770", "Intime Beziehungen", "Intimate relationships", "Activities"),
    ("d845", "Eine Arbeitsstelle erlangen, behalten und beenden", "Acquiring, keeping and terminating a job", "Activities"),
    ("d850", "Bezahlte Taetigkeit", "Remunerative employment", "Activities"),
    ("d855", "Unbezahlte Taetigkeit", "Non-remunerative employment", "Activities"),
    ("d860", "Elementare wirtschaftliche Transaktionen", "Basic economic transactions", "Activities"),
    ("d870", "Wirtschaftliche Eigenstaendigkeit", "Economic self-sufficiency", "Activities"),
    ("d910", "Gemeinschaftsleben", "Community life", "Activities"),
    ("d920", "Erholung und Freizeit", "Recreation and leisure", "Activities"),

    # --- Environmental Factors (e) ---
    ("e110", "Produkte und Substanzen fuer den persoenlichen Gebrauch", "Products or substances for personal consumption", "Environmental"),
    ("e115", "Produkte und Technologien zum persoenlichen Gebrauch im taeglichen Leben", "Products and technology for personal use in daily living", "Environmental"),
    ("e120", "Produkte und Technologien zur persoenlichen Mobilitaet", "Products and technology for personal indoor and outdoor mobility and transportation", "Environmental"),
    ("e150", "Entwurf, Konstruktion und Bauprodukte", "Design, construction and building products and technology of buildings for public use", "Environmental"),
    ("e310", "Engster Familienkreis", "Immediate family", "Environmental"),
    ("e315", "Erweiterter Familienkreis", "Extended family", "Environmental"),
    ("e320", "Freunde", "Friends", "Environmental"),
    ("e325", "Bekannte, Seinesgleichen, Kollegen, Nachbarn", "Acquaintances, peers, colleagues, neighbours and community members", "Environmental"),
    ("e330", "Autoritaetspersonen", "People in positions of authority", "Environmental"),
    ("e340", "Persoenliche Hilfs- und Pflegepersonen", "Personal care providers and personal assistants", "Environmental"),
    ("e355", "Fachleute der Gesundheitsberufe", "Health professionals", "Environmental"),
    ("e360", "Andere Fachleute", "Other professionals", "Environmental"),
    ("e410", "Individuelle Einstellungen der Mitglieder des engsten Familienkreises", "Individual attitudes of immediate family members", "Environmental"),
    ("e420", "Individuelle Einstellungen von Freunden", "Individual attitudes of friends", "Environmental"),
    ("e450", "Individuelle Einstellungen von Fachleuten der Gesundheitsberufe", "Individual attitudes of health professionals", "Environmental"),
    ("e460", "Gesellschaftliche Einstellungen", "Societal attitudes", "Environmental"),
    ("e465", "Gesellschaftliche Normen, Konventionen und Weltanschauungen", "Social norms, practices and ideologies", "Environmental"),
    ("e525", "Dienste, Systeme und Handlungsgrundsaetze des Wohnungswesens", "Housing services, systems and policies", "Environmental"),
    ("e535", "Dienste, Systeme und Handlungsgrundsaetze des Kommunikationswesens", "Communication services, systems and policies", "Environmental"),
    ("e540", "Dienste, Systeme und Handlungsgrundsaetze des Transportwesens", "Transportation services, systems and policies", "Environmental"),
    ("e550", "Dienste, Systeme und Handlungsgrundsaetze der Rechtspflege", "Legal services, systems and policies", "Environmental"),
    ("e570", "Dienste, Systeme und Handlungsgrundsaetze der sozialen Sicherheit", "Social security services, systems and policies", "Environmental"),
    ("e575", "Dienste, Systeme und Handlungsgrundsaetze der allgemeinen sozialen Unterstuetzung", "General social support services, systems and policies", "Environmental"),
    ("e580", "Dienste, Systeme und Handlungsgrundsaetze des Gesundheitswesens", "Health services, systems and policies", "Environmental"),
    ("e590", "Dienste, Systeme und Handlungsgrundsaetze des Arbeits- und Beschaeftigungswesens", "Labour and employment services, systems and policies", "Environmental"),
]


# ===================================================================
# CROSS-MAPPING: DSM-5-TR (ICD-10-CM) <-> ICD-11
# ===================================================================

MAPPINGS = [
    # Neurodevelopmental
    ("dsm5", "F84.0", "icd11", "6A02", "equivalent"),    # ASD
    ("dsm5", "F90.0", "icd11", "6A05.0", "equivalent"),   # ADHD inattentive
    ("dsm5", "F90.1", "icd11", "6A05.1", "equivalent"),   # ADHD hyperactive
    ("dsm5", "F90.2", "icd11", "6A05.2", "equivalent"),   # ADHD combined
    ("dsm5", "F70", "icd11", "6A00.0", "equivalent"),     # Mild ID
    ("dsm5", "F71", "icd11", "6A00.1", "equivalent"),     # Moderate ID
    ("dsm5", "F72", "icd11", "6A00.2", "equivalent"),     # Severe ID
    ("dsm5", "F95.2", "icd11", "8A05.00", "narrower"),    # Tourette

    # Schizophrenia spectrum
    ("dsm5", "F20.9", "icd11", "6A20", "equivalent"),     # Schizophrenia
    ("dsm5", "F25.0", "icd11", "6A21", "narrower"),       # Schizoaffective bipolar
    ("dsm5", "F25.1", "icd11", "6A21", "narrower"),       # Schizoaffective depressive
    ("dsm5", "F21", "icd11", "6A22", "equivalent"),        # Schizotypal
    ("dsm5", "F23", "icd11", "6A23", "equivalent"),        # Brief psychotic
    ("dsm5", "F22", "icd11", "6A24", "equivalent"),        # Delusional

    # Mood: Bipolar
    ("dsm5", "F31.11", "icd11", "6A60.0", "narrower"),    # Bipolar I manic
    ("dsm5", "F31.2", "icd11", "6A60.1", "equivalent"),   # Bipolar I manic + psychosis
    ("dsm5", "F31.31", "icd11", "6A60.2", "narrower"),    # Bipolar I depressed mild
    ("dsm5", "F31.32", "icd11", "6A60.3", "narrower"),    # Bipolar I depressed moderate
    ("dsm5", "F31.4", "icd11", "6A60.5", "equivalent"),   # Bipolar I depressed severe
    ("dsm5", "F31.5", "icd11", "6A60.5", "narrower"),     # Bipolar I depressed severe + psychosis
    ("dsm5", "F31.81", "icd11", "6A61", "equivalent"),    # Bipolar II
    ("dsm5", "F34.0", "icd11", "6A62", "equivalent"),     # Cyclothymia

    # Mood: Depression
    ("dsm5", "F32.0", "icd11", "6A70.0", "equivalent"),   # MDD single mild
    ("dsm5", "F32.1", "icd11", "6A70.1", "equivalent"),   # MDD single moderate
    ("dsm5", "F32.2", "icd11", "6A70.3", "equivalent"),   # MDD single severe
    ("dsm5", "F32.3", "icd11", "6A70.4", "equivalent"),   # MDD single severe + psychosis
    ("dsm5", "F33.0", "icd11", "6A71.0", "equivalent"),   # MDD recurrent mild
    ("dsm5", "F33.1", "icd11", "6A71.1", "equivalent"),   # MDD recurrent moderate
    ("dsm5", "F33.2", "icd11", "6A71.3", "equivalent"),   # MDD recurrent severe
    ("dsm5", "F33.3", "icd11", "6A71.4", "equivalent"),   # MDD recurrent severe + psychosis
    ("dsm5", "F34.1", "icd11", "6A72", "equivalent"),     # Dysthymia

    # Anxiety
    ("dsm5", "F41.1", "icd11", "6B00", "equivalent"),     # GAD
    ("dsm5", "F41.0", "icd11", "6B01", "equivalent"),     # Panic
    ("dsm5", "F40.00", "icd11", "6B02", "equivalent"),    # Agoraphobia
    ("dsm5", "F40.10", "icd11", "6B04", "equivalent"),    # Social anxiety
    ("dsm5", "F40.218", "icd11", "6B03", "narrower"),     # Specific phobia
    ("dsm5", "F93.0", "icd11", "6B05", "equivalent"),     # Separation anxiety
    ("dsm5", "F94.0", "icd11", "6B06", "equivalent"),     # Selective mutism

    # OCD
    ("dsm5", "F42.2", "icd11", "6B20", "equivalent"),     # OCD
    ("dsm5", "F45.22", "icd11", "6B21", "equivalent"),    # Body dysmorphic
    ("dsm5", "F42.3", "icd11", "6B24", "equivalent"),     # Hoarding
    ("dsm5", "F63.3", "icd11", "6B25.0", "equivalent"),   # Trichotillomania
    ("dsm5", "L98.1", "icd11", "6B25.1", "equivalent"),   # Excoriation

    # Stress-related
    ("dsm5", "F43.10", "icd11", "6B40", "equivalent"),    # PTSD
    ("dsm5", "F43.21", "icd11", "6B43", "narrower"),      # Adjustment depressed
    ("dsm5", "F43.22", "icd11", "6B43", "narrower"),      # Adjustment anxiety
    ("dsm5", "F43.23", "icd11", "6B43", "narrower"),      # Adjustment mixed
    ("dsm5", "F94.1", "icd11", "6B44", "equivalent"),     # Reactive attachment
    ("dsm5", "F94.2", "icd11", "6B45", "equivalent"),     # Disinhibited social engagement

    # Dissociative
    ("dsm5", "F44.81", "icd11", "6B64", "equivalent"),    # DID
    ("dsm5", "F44.0", "icd11", "6B61", "equivalent"),     # Dissociative amnesia
    ("dsm5", "F48.1", "icd11", "6B66", "equivalent"),     # Depersonalization

    # Eating
    ("dsm5", "F50.01", "icd11", "6B80.0", "equivalent"),  # Anorexia restricting
    ("dsm5", "F50.02", "icd11", "6B80.1", "equivalent"),  # Anorexia binge-purge
    ("dsm5", "F50.2", "icd11", "6B81", "equivalent"),     # Bulimia
    ("dsm5", "F50.81", "icd11", "6B82", "equivalent"),    # Binge eating
    ("dsm5", "F50.82", "icd11", "6B83", "equivalent"),    # ARFID

    # Substance use (main categories)
    ("dsm5", "F10.20", "icd11", "6C40.2", "equivalent"),  # Alcohol dependence
    ("dsm5", "F12.20", "icd11", "6C41.2", "equivalent"),  # Cannabis dependence
    ("dsm5", "F11.20", "icd11", "6C43.2", "equivalent"),  # Opioid dependence
    ("dsm5", "F13.20", "icd11", "6C44.2", "equivalent"),  # Sedative dependence
    ("dsm5", "F14.20", "icd11", "6C45.2", "equivalent"),  # Cocaine dependence
    ("dsm5", "F15.20", "icd11", "6C46.2", "equivalent"),  # Stimulant dependence
    ("dsm5", "F17.200", "icd11", "6C4A.2", "equivalent"), # Nicotine dependence

    # Personality (DSM-5 categorical -> ICD-11 dimensional)
    ("dsm5", "F60.3", "icd11", "6D10", "broader"),        # Borderline -> PD (ICD-11 dimensional)
    ("dsm5", "F60.2", "icd11", "6D10", "broader"),        # Antisocial -> PD
    ("dsm5", "F60.81", "icd11", "6D10", "broader"),       # Narcissistic -> PD
    ("dsm5", "F60.6", "icd11", "6D10", "broader"),        # Avoidant -> PD
    ("dsm5", "F60.7", "icd11", "6D10", "broader"),        # Dependent -> PD
    ("dsm5", "F60.5", "icd11", "6D10", "broader"),        # OCPD -> PD
    ("dsm5", "F60.4", "icd11", "6D10", "broader"),        # Histrionic -> PD
    ("dsm5", "F60.0", "icd11", "6D10", "broader"),        # Paranoid -> PD
    ("dsm5", "F60.1", "icd11", "6D10", "broader"),        # Schizoid -> PD

    # Neurocognitive
    ("dsm5", "F05", "icd11", "6D70", "equivalent"),        # Delirium
    ("dsm5", "G30.9", "icd11", "6D80", "equivalent"),     # Alzheimer
    ("dsm5", "F01.50", "icd11", "6D81", "equivalent"),    # Vascular dementia
    ("dsm5", "G31.83", "icd11", "6D82", "equivalent"),    # Lewy body dementia
    ("dsm5", "G31.09", "icd11", "6D83", "equivalent"),    # Frontotemporal dementia

    # Sleep
    ("dsm5", "G47.00", "icd11", "7A00", "equivalent"),    # Insomnia
    ("dsm5", "G47.10", "icd11", "7A01", "equivalent"),    # Hypersomnolence
    ("dsm5", "G47.411", "icd11", "7A20", "equivalent"),   # Narcolepsy

    # Gender
    ("dsm5", "F64.0", "icd11", "HA60", "equivalent"),     # Gender dysphoria adults
    ("dsm5", "F64.2", "icd11", "HA61", "equivalent"),     # Gender dysphoria children

    # Impulse control
    ("dsm5", "F63.0", "icd11", "6C50", "equivalent"),     # Gambling
    ("dsm5", "F63.1", "icd11", "6C70", "equivalent"),     # Pyromania
    ("dsm5", "F63.2", "icd11", "6C71", "equivalent"),     # Kleptomania
    ("dsm5", "F63.81", "icd11", "6C72", "equivalent"),    # IED

    # Disruptive
    ("dsm5", "F91.3", "icd11", "6C90", "equivalent"),     # ODD
    ("dsm5", "F91.1", "icd11", "6C91", "narrower"),       # Conduct disorder
]


# ===================================================================
# BUILD DATABASE
# ===================================================================

def build():
    from datetime import date

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"[INFO] Alte Datenbank geloescht: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()

        # Schema
        cur.executescript(SCHEMA)
        print("[OK] Schema erstellt")

        # ICD-11
        all_icd11 = ICD11_PSYCHIATRIC + ICD11_SLEEP + ICD11_GENDER + ICD11_MEDICAL
        cur.executemany(
            "INSERT OR REPLACE INTO icd11 (code, title_de, title_en, chapter, block) VALUES (?,?,?,?,?)",
            all_icd11
        )
        print(f"[OK] {len(all_icd11)} ICD-11-Codes eingefuegt")

        # DSM-5-TR
        cur.executemany(
            "INSERT OR REPLACE INTO dsm5 (icd10cm_code, title_de, title_en, dsm5_category) VALUES (?,?,?,?)",
            DSM5_DATA
        )
        print(f"[OK] {len(DSM5_DATA)} DSM-5-TR-Codes eingefuegt")

        # ICF
        cur.executemany(
            "INSERT OR REPLACE INTO icf (code, title_de, title_en, component) VALUES (?,?,?,?)",
            ICF_DATA
        )
        print(f"[OK] {len(ICF_DATA)} ICF-Codes eingefuegt")

        # Cross-Mapping
        cur.executemany(
            "INSERT INTO code_mapping (source_system, source_code, target_system, target_code, mapping_quality) VALUES (?,?,?,?,?)",
            MAPPINGS
        )
        print(f"[OK] {len(MAPPINGS)} Cross-Mappings eingefuegt")

        # Metadata
        cur.executemany("INSERT OR REPLACE INTO metadata (key, value) VALUES (?,?)", [
            ("version", "1.0"),
            ("build_date", str(date.today())),
            ("scope", "psychiatry_focus"),
            ("icd11_count", str(len(all_icd11))),
            ("dsm5_count", str(len(DSM5_DATA))),
            ("icf_count", str(len(ICF_DATA))),
            ("mapping_count", str(len(MAPPINGS))),
        ])

        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Datenbankaufbau fehlgeschlagen: {e}")
        raise
    finally:
        conn.close()

    size_kb = os.path.getsize(DB_PATH) / 1024
    total = len(all_icd11) + len(DSM5_DATA) + len(ICF_DATA)
    print(f"\n{'='*60}")
    print(f"Datenbank erstellt: {DB_PATH}")
    print(f"Groesse: {size_kb:.0f} KB")
    print(f"Gesamt: {total} Codes + {len(MAPPINGS)} Mappings")
    print(f"{'='*60}")


if __name__ == "__main__":
    build()
