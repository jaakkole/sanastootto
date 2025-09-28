import streamlit as st
import requests
import csv
import difflib
from io import StringIO
import random

def load_vocab_from_url(url):
    import csv
    from io import StringIO

    vocab = {}

    # Suora latauslinkki
    dl_url = (
        url.replace("?dl=0", "?dl=1")
           .replace("?raw=1", "?dl=1")
    )

    try:
        resp = requests.get(dl_url, timeout=15)
        resp.raise_for_status()

        # Merkistön automaattinen valinta
        content = None
        for enc in ("utf-8", "utf-8-sig", "cp1252", "iso-8859-1"):
            try:
                content = resp.content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if content is None:
            raise UnicodeError("Tuntematon merkistö (kokeiltu utf-8, utf-8-sig, cp1252, iso-8859-1)")

        # Erotin tunnistus
        sample = content[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ";" if (";" in sample and "," not in sample) else ","

        f = StringIO(content)
        reader = csv.DictReader(f, delimiter=delimiter)

        # Otsikoiden normalisointi
        fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
        field_map = {fn.lower(): fn for fn in fieldnames}
        fi_col = next((field_map[k] for k in ("finnish", "suomi", "fi") if k in field_map), None)
        en_col = next((field_map[k] for k in ("english", "englanti", "en") if k in field_map), None)
        if not fi_col or not en_col:
            raise KeyError(f"Tarvitaan sarakkeet 'finnish' ja 'english' (löydetyt: {fieldnames})")

        for row in reader:
            fi = (row.get(fi_col, "") or "").strip().lower()
            en = (row.get(en_col, "") or "").strip().lower()
            if fi and en:
                vocab[fi] = en

    except Exception as e:
        st.error(f"CSV-tiedoston lataus epäonnistui: {e}")

    return vocab


def check_answer(user_answer, correct_answer):
    user_answer = user_answer.strip().lower()
    if user_answer == correct_answer:
        return "correct"
    else:
        similarity = difflib.SequenceMatcher(None, user_answer, correct_answer).ratio()
        if similarity > 0.7:
            return "close"
        else:
            return "wrong"

def main():
    st.title("Sanaston harjoittelija – Otto")
    st.write("Tämä sovellus kysyy sinulta käännöksiä suomenkielisille sanoille.")

    # 🔁 VAIHDA TÄMÄ OMAAN DROPBOX-LINKKIISI
    csv_url = "https://www.dropbox.com/scl/fi/0re5cxtkm5qvnvp8fw30n/otto.csv?rlkey=urjiadm3pcgpx32f0q9pr1hiy&dl=1"

    vocab = load_vocab_from_url(csv_url)

    if not vocab:
        st.warning("Sanastoa ei löytynyt tai CSV-tiedosto on tyhjä.")
        return

    if 'words' not in st.session_state or len(st.session_state.words) == 0:
        st.session_state.words = list(vocab.keys())
        random.shuffle(st.session_state.words)
        st.session_state.index = 0
        st.session_state.correct_count = 0
        st.session_state.total_count = 0
        st.session_state.show_feedback = False
        st.session_state.last_result = None
        st.session_state.correct_answer = ""
        st.session_state.answer = ""

    def submit_answer():
        if st.session_state.answer.strip() == "":
            st.warning("Kirjoita vastaus ennen lähettämistä!")
            return
        current_word = st.session_state.words[st.session_state.index]
        correct_answer = vocab[current_word]
        result = check_answer(st.session_state.answer, correct_answer)
        st.session_state.last_result = result
        st.session_state.correct_answer = correct_answer
        st.session_state.show_feedback = True
        st.session_state.total_count += 1
        if result == "correct":
            st.session_state.correct_count += 1

    def next_word():
        st.session_state.index += 1
        st.session_state.show_feedback = False
        st.session_state.last_result = None
        st.session_state.correct_answer = ""
        st.session_state.answer = ""

    if st.session_state.index >= len(st.session_state.words):
        st.write("Olet käynyt kaikki sanat läpi!")
        st.write(f"Yhteensä oikein: {st.session_state.correct_count} / {st.session_state.total_count}")
        if st.button("Aloita alusta"):
            st.session_state.words = []
            st.session_state.index = 0
            st.session_state.correct_count = 0
            st.session_state.total_count = 0
            st.session_state.show_feedback = False
            st.session_state.last_result = None
            st.session_state.correct_answer = ""
            st.session_state.answer = ""
        return

    current_word = st.session_state.words[st.session_state.index]
    st.markdown(f"<span style='color:red; font-weight:bold; font-size:24px;'>Käännä sana: {current_word}</span>", unsafe_allow_html=True)

    if not st.session_state.show_feedback:
        with st.form(key='answer_form', clear_on_submit=False):
            st.text_input("Kirjoita englanniksi:", key="answer")
            submitted = st.form_submit_button("Vastaa", on_click=submit_answer)
    else:
        if st.session_state.last_result == "correct":
            st.success("Hienoa! Oikein meni.")
        elif st.session_state.last_result == "close":
            st.info(f"Hyvä hyvä, mutta vähän väärin. Oikea vastaus on: {st.session_state.correct_answer}")
        else:
            st.error(f"Väärin. Oikea vastaus on: {st.session_state.correct_answer}")

        st.write(f"Edistys: {st.session_state.index + 1} / {len(st.session_state.words)}")
        st.write(f"Oikein tähän mennessä: {st.session_state.correct_count}")

        if st.button("Seuraava sana", on_click=next_word):
            pass

if __name__ == "__main__":
    main()




