from dataclasses import dataclass


@dataclass(frozen=True)
class Court_Case_Data:
    sr_no:str
    case_detail:str
    case_type:str
    case_no:str
    case_year:str
    party_name:str
    petitioner:str
    respondent:str
    bench:str
    case_category:str

