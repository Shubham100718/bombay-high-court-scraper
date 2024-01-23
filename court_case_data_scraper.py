import os, requests, time
from bs4 import BeautifulSoup
from typing import Optional, List
from court_case_dataclass import Court_Case_Data
from headers import starting_page_headers, html_page_headers, pagination_headers


class Court_Case_Scraper:
    
    def __init__(self, input_data:dict, proxy:dict = {}, debug:bool = False) -> None:
        
        self.input_data = input_data
        self.debug = debug 
        self.session = requests.Session()
        self.session.proxies.update(proxy)
        self.all_court_case_data = []

    def __save_html_page(self, starting_page_response:Optional[requests.session]) -> None:
        
        current_wroking_dir = os.getcwd()
        with open(f"{current_wroking_dir}/front_page.html", "wb") as html_file:
            html_file.write(starting_page_response.content)

    def __extract_fields(self, soup:Optional[BeautifulSoup], selector:str) -> None:

        if selector=="HTML":
            captcha_text = soup.select('img#captchaimg')[0].get('src').split('=')[1]
            payload_data = soup.select('form>input')
            csrf_name = payload_data[0].get('value')
            csrf_token = payload_data[1].get('value')

            court_cases_payload = f"CSRFName={csrf_name}&CSRFToken={csrf_token}&m_hc={self.input_data.get('court_code')}&m_side={self.input_data.get('case_side')}&pageno=1&m_party={self.input_data.get('party_name')}&petres={self.input_data.get('party_type')}&myr={self.input_data.get('case_year')}&captchaflg=&captcha_code={captcha_text}&submit1=Submit"

            court_cases_response = self.session.post("https://bombayhighcourt.nic.in/partyquery_action.php", headers=html_page_headers, data=court_cases_payload)
            soup = BeautifulSoup(court_cases_response.content, 'lxml')
            if soup.select('div.table.table-responsive>table>tr>td') != []:
                party_data_list = soup.select('div.table.table-responsive>table>tr')[2:]
        
        elif selector=='API':
            if soup.select('div.table-responsive>table>table>tr>td') == []:
                party_data_list = soup.select('div.table-responsive>table>tr')

        for raw_tags_data in party_data_list:
            raw_tag_data_list = raw_tags_data.select('td')
            if raw_tag_data_list != []:
                sr_no = raw_tag_data_list[0].select('font')[0].get_text(strip=True).replace('.','')
                petitioner = raw_tag_data_list[0].select('b')[0].get_text(strip=True)
                respondent = raw_tag_data_list[0].select('b')[1].get_text(strip=True)
                party_name = petitioner + ' V/S ' + respondent
                bench = raw_tag_data_list[1].get_text(strip=True)
                case_detail = raw_tag_data_list[2].get_text(strip=True)
                case_type = case_detail.split('/')[0].strip()
                case_no = case_detail.split('/')[1].strip()
                case_year = case_detail.split('/')[2].strip().split('(')[0].strip()
                try: 
                    case_detail.split('/')[2].strip().split('(')[1].split(')')[0].strip() == 'stamp'
                    case_category = 'Stamp'
                except:
                    case_category = 'Register'

                self.all_court_case_data.append(Court_Case_Data(sr_no,case_detail,case_type,case_no,case_year,party_name,petitioner,respondent,bench,case_category))

    def __extract_data_from_paginattion(self) -> Optional[BeautifulSoup]:
                
        count = 100
        while True:
            time.sleep(0.01)
            paginattion_payload = f"id={count}&HC={self.input_data.get('court_code')}&TYPE={self.input_data.get('party_type')}&PARTY={self.input_data.get('party_name')}&YEAR={self.input_data.get('case_year')}&SIDE={self.input_data.get('case_side')}"
                        
            paginattion_response = self.session.post("https://bombayhighcourt.nic.in/ajax_loadmore_party.php", headers=pagination_headers, data=paginattion_payload)

            pagination_soup = BeautifulSoup(paginattion_response.content, 'lxml')

            if pagination_soup.select('div.table-responsive>table>tr') != []:
            
                self.__extract_fields(pagination_soup, "API")
                count += 100
            else:
                break

    def __extract_data_from_html(self) -> Optional[BeautifulSoup]:
        
        starting_page_response = self.session.get('https://bombayhighcourt.nic.in/party_query.php', headers=starting_page_headers)

        if self.debug:
            self.__save_html_page(starting_page_response)
            
        soup = BeautifulSoup(starting_page_response.content, 'html.parser')

        self.__extract_fields(soup, "HTML")
        
        return soup

    def start(self) -> Optional[List[Court_Case_Data]]:
        
        self.__extract_data_from_html()
        self.__extract_data_from_paginattion()

        return self.all_court_case_data


if __name__ == '__main__':
    input_data = {
        "court_code": "01",
        "case_side": "C",
        "party_name": "sharma",
        "party_type": "P",
        "case_year": "2023"
    }
    print(Court_Case_Scraper(input_data).start())

