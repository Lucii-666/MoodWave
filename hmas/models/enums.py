"""
hmas.models.enums
─────────────────
Categorical domain enums derived from the MER-1M dataset.
Every string enum mirrors the exact values found in MD-1M.csv so that
Pydantic validation catches data-quality issues at parse time.
"""

from enum import Enum


# ── Musical / Audio ──────────────────────────────────────────────────────────

class Mode(str, Enum):
    MAJOR = "Major"
    MINOR = "Minor"


class Genre(str, Enum):
    ACOUSTIC    = "Acoustic"
    ALTERNATIVE = "Alternative"
    BLUES       = "Blues"
    COUNTRY     = "Country"
    DANCE       = "Dance"
    DISCO       = "Disco"
    ELECTRONIC  = "Electronic"
    FOLK        = "Folk"
    FUNK        = "Funk"
    HIP_HOP     = "Hip-Hop"
    HOUSE       = "House"
    INDIE       = "Indie"
    JAZZ        = "Jazz"
    METAL       = "Metal"
    POP         = "Pop"
    RNB         = "R&B"
    ROCK        = "Rock"
    SOUL        = "Soul"


class SubGenre(str, Enum):
    ALTERNATIVE_ROCK = "Alternative Rock"
    AMBIENT          = "Ambient"
    ART_POP          = "Art Pop"
    BOOM_BAP         = "Boom Bap"
    CLASSIC          = "Classic"
    CLASSIC_ROCK     = "Classic Rock"
    CONSCIOUS        = "Conscious"
    CONTEMPORARY_RNB = "Contemporary R&B"
    DANCE_POP        = "Dance-Pop"
    DUBSTEP          = "Dubstep"
    EDM              = "EDM"
    ELECTROPOP       = "Electropop"
    HARD_ROCK        = "Hard Rock"
    LO_FI            = "Lo-Fi"
    MODERN           = "Modern"
    NEO_SOUL         = "Neo-Soul"
    PUNK_ROCK        = "Punk Rock"
    QUIET_STORM      = "Quiet Storm"
    SOFT_ROCK        = "Soft Rock"
    STANDARD         = "Standard"
    SYNTH_POP        = "Synth-Pop"
    TEEN_POP         = "Teen Pop"
    TRANCE           = "Trance"
    TRAP             = "Trap"


class StructuralPattern(str, Enum):
    AABA                = "AABA"
    STROPHIC            = "Strophic"
    THROUGH_COMPOSED    = "Through-Composed"
    VERSE_CHORUS_BRIDGE = "Verse-Chorus-Bridge"
    VERSE_CHORUS_VERSE  = "Verse-Chorus-Verse"


class NarrativeArc(str, Enum):
    COMEDY        = "Comedy"
    QUEST         = "Quest"
    RAGS_TO_RICHES = "Rags to Riches"
    REBIRTH       = "Rebirth"
    REDEMPTION    = "Redemption"
    SLICE_OF_LIFE = "Slice of Life"
    TRAGEDY       = "Tragedy"


# ── Emotion ──────────────────────────────────────────────────────────────────

class Emotion(str, Enum):
    ANGER       = "Anger"
    BITTERSWEET = "Bittersweet"
    DEFIANCE    = "Defiance"
    EMPOWERMENT = "Empowerment"
    EUPHORIA    = "Euphoria"
    EXCITEMENT  = "Excitement"
    FEAR        = "Fear"
    HOPE        = "Hope"
    JOY         = "Joy"
    LONGING     = "Longing"
    LOVE        = "Love"
    MELANCHOLY  = "Melancholy"
    NOSTALGIA   = "Nostalgia"
    PASSION     = "Passion"
    PEACE       = "Peace"
    SADNESS     = "Sadness"
    SERENITY    = "Serenity"


# ── Contextual / Behavioural ────────────────────────────────────────────────

class AlbumType(str, Enum):
    COMPILATION  = "Compilation"
    EP           = "EP"
    LIVE_ALBUM   = "Live Album"
    SINGLE       = "Single"
    SOUNDTRACK   = "Soundtrack"
    STUDIO_ALBUM = "Studio Album"


class PlaylistContext(str, Enum):
    BEACH_DAY       = "Beach Day"
    CHILL           = "Chill"
    EVENING_WIND    = "Evening Wind Down"
    FOCUS           = "Focus"
    LATE_NIGHT      = "Late Night Vibes"
    MORNING_ROUTINE = "Morning Routine"
    PARTY           = "Party"
    RAINY_DAY       = "Rainy Day"
    ROAD_TRIP       = "Road Trip"
    ROMANCE         = "Romance"
    SLEEP           = "Sleep"
    STUDY_SESSION   = "Study Session"
    WORKOUT         = "Workout"


class ListeningTime(str, Enum):
    AFTERNOON  = "Afternoon"
    ANY_TIME   = "Any Time"
    EVENING    = "Evening"
    LATE_NIGHT = "Late Night"
    MORNING    = "Morning"
    NIGHT      = "Night"


class SeasonalRelevance(str, Enum):
    AUTUMN     = "Autumn"
    MONSOON    = "Monsoon"
    SPRING     = "Spring"
    SUMMER     = "Summer"
    WINTER     = "Winter"
    YEAR_ROUND = "Year-Round"


# ── Energy Label (classification target) ─────────────────────────────────────

class EnergyLabel(str, Enum):
    """
    Discretised energy level predicted by the Classification Agent.
    Boundaries are configurable in hmas.config.
    """
    LOW       = "Low"
    MEDIUM    = "Medium"
    HIGH      = "High"
    VERY_HIGH = "Very High"
