import logging
import sys
import time
import random
from api.API import API
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.PlayerInformation import PlayerInformation

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("sinoalice.log", "w", "utf-8")
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %I:%M:%S')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)


common_names = ["Ninja", "Ryu", "Nathan", "Ashley", "Kasumi", "Leon", "Adam", "Shepard",
                "James", "John", "David", "Richard", "Maria", "Donald"]


class Bot:
    def __init__(self):
        self.api = API()

    def create_new_account(self, must_char_list, must_item_list):
        self.api.login(new_registration=True)

        self.api.POST__api_user_get_user_data()
        self.api.POST__api_config_get_config()
        self.api.POST__api_tutorial_get_next_tutorial_mst_id()
        self.api.POST__api_tutorial_agree_legal_document()
        self.api.POST__api_tutorial_get_user_mini_tutorial_data()
        self.api.POST__api_tutorial_get_tutorial_gacha()

        # Loop
        num_ssrare = 0
        num_characters = 0
        while num_ssrare < 1 and num_characters < 3:
            time.sleep(11)
            num_ssrare, num_srare, num_characters, item_names = self.api.POST__api_tutorial_fxm_tutorial_gacha_drawn_result()

        self.api.POST__api_tutorial_fxm_tutorial_gacha_exec()
        # Loop End

        name = random.choice(common_names)
        self.api.POST__api_tutorial_set_user_name(name)
        self.api.POST__api_tutorial_set_character(2)
        # Missions
        self.api.POST__api_cleaning_check()
        self.api.POST__api_cleaning_start()
        self.api.POST__api_cleaning_end_wave(25, 1, 5, 5, 5)
        self.api.POST__api_cleaning_end_wave(20, 2, 4, 4, 4)
        self.api.POST__api_cleaning_end_wave(17, 3, 6, 6, 6)
        self.api.POST__api_cleaning_end_wave(14, 4, 6, 6, 6)
        self.api.POST__api_cleaning_end_wave(11, 5, 7, 7, 7)
        self.api.POST__api_cleaning_end_wave(11, 6, 7, 16, 7)
        self.api.POST__api_cleaning_end_wave(6, 7, 0, 16, 7)
        self.api.POST__api_cleaning_end_wave(3, 8, 0, 7, 7)
        self.api.POST__api_cleaning_end_wave(0, 9, 0, 4, 4)
        self.api.POST__api_cleaning_end(10)
        # Missions done
        self.api.POST__api_user_get_user_data()
        self.api.POST__api_tutorial_get_next_tutorial_mst_id()
        self.api.POST__api_cleaning_retire()

    def finish_first_quest(self):
        self.api.POST__api_quest_get_attention()
        self.api.POST__api_quest_get_alice_area_map()
        self.api.POST__api_quest_get_alice_stage_list()
        self.api.POST__api_quest_get_stage_reward()
        self.api.POST__api_quest_get_stage_data()
        self.api.POST__api_quest_get_tutorial_result()

    def get_all_presents(self):
        present_list = self.api.POST__api_present_get_present_data()
        self.api.POST__api_present_gain_present(present_list)

    def play_gacha(self, gacha_id):
        self.api.POST__api_gacha_gacha_exec()
        self.api.POST__api_gacha_gacha_exec()
        self.api.POST__api_gacha_gacha_exec()

    def is_good_account(self):
        chars, chars_ids = self.api.POST__api_character_get_character_data_list()
        items, nightmares, ids = self.api.POST__api_card_info_get_card_data_by_user_id()
        logging.info(nightmares)
        logging.info(items)
        logging.info(chars)
        logging.debug(chars_ids)
        logging.debug(ids)

    def migrate(self):
        # Migration
        self.api.get_migrate_information("COSInu11")


def reroll_good_account():
    tutorial_chars = []
    tutorial_items = []
    gacha_items = []
    gacha_chars = []

    bot = Bot()
    bot.create_new_account()
    bot.finish_first_quest()
    bot.get_all_presents()
    bot.play_gacha(1)
    bot.is_good_account()
    bot.migrate()
    exit(1)
    return player_information


if __name__ == "__main__":
    db_name = "sinoalice_accounts.db"
    PlayerInformation.create_db(db_name)
    engine = create_engine(f"sqlite:///{db_name}")
    Session = sessionmaker(bind=engine)
    session = Session()

    future_list = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        for _ in range(1000):
            future = executor.submit(reroll_good_account)
            future_list.append(future)

        for future in as_completed(future_list):
            try:
                player_information = future.result()
                if player_information:
                    session.add(player_information)
                    session.commit()
            except Exception as e:
                logging.warning("An exception occurred, to many threads?")
                print(e)

    logging.info("Finished")