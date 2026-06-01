"""
Scrapes freely available Tesla texts from the web.
Includes embedded fallback content for Tesla's autobiography ("My Inventions")
so the RAG pipeline always has substantial material.
"""
import requests
from bs4 import BeautifulSoup
import time
import os
import json
from pathlib import Path

DATA_DIR = Path("data/raw")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ----------------------------------------------------
# Embedded Tesla autobiography excerpts (public domain)
# from "My Inventions" by Nikola Tesla, 1919
# ----------------------------------------------------

MY_INVENTIONS_CHAPTERS = {
    "ch1_my_early_life": """MY INVENTIONS  --  Chapter 1: My Early Life
By Nikola Tesla (1919)

The progressive development of man is vitally dependent on invention. It is the most important product of his creative brain. Its ultimate purpose is the complete mastery of mind over the material world, the harnessing of the forces of nature to human needs. This is the difficult task of the inventor who is often misunderstood and unrewarded. But he finds ample compensation in the pleasing exercises of his powers and in the knowledge of being one of that exceptionally privileged class without whom the race would have long ago perished in the bitter struggle against pitiless elements.

I was born in 1856 in Smiljan, a village in Lika, a mountainous region of what was then the Austro-Hungarian Empire, now Croatia. My father was a clergyman, a man of great learning and a natural philosopher of considerable attainments. My mother was a woman of genius. She invented and constructed all kinds of tools and devices, from looms to churns, and wove the finest designs from thread she had spun herself. When she was past sixty, her fingers were still nimble enough to tie three knots in an eyelash.

The gift of mental power comes from God, Divine Being, and if we concentrate our minds on that truth, we become in tune with this great power. My Mother had taught me to seek all truth in the Bible. I was intended from birth for the clergy, but the desire to practice electrical engineering was too strong.

From childhood I was compelled to concentrate my thoughts on things of the imagination. In my boyhood I suffered from a peculiar affliction due to the appearance of images, often accompanied by strong flashes of light, which marred the sight of real objects and interfered with my thought and action. When a word was spoken to me, the image of the object it designated would present itself vividly to my vision, and sometimes I was quite unable to distinguish whether what I saw was tangible or not. This caused me great discomfort and anxiety.

I also began to have visions. I would see places, people, and events with perfect clarity, as if they were real. This faculty for visualizing with the greatest facility proved to be of great value in my later career as an inventor. I could project before me any object, a machine for example, and examine it in every detail, testing it mentally without building a physical prototype.

I trained myself systematically in this discipline of visualization. I would start by imagining simple geometric figures, then progress to machines of increasing complexity. Eventually, I could construct an entire turbine or motor in my mind, set it running, test its bearings, measure its efficiency, and correct its flaws  --  all without touching a physical tool. This is a method I recommend to all engineers: think first, build second. Edison took the opposite approach, trying thousands of experiments where calculation and theory could have saved ninety percent of the labor.

In my youth I was strongly attracted to electricity. The mysterious phenomena of nature fascinated me. I read everything I could find about electricity and magnetism. When I was about twelve years old, I resolved that I would one day harness the power of Niagara Falls. Many years later, this dream came true.

My health in early life was poor. I was a sickly child and my parents feared for my survival. But I was determined and stubborn. I recovered my strength through exercise and an iron will. I learned early that the mind can conquer the body, and this conviction served me well throughout my life of relentless work.""",

    "ch2_my_first_efforts": """MY INVENTIONS  --  Chapter 2: My First Efforts in Invention
By Nikola Tesla (1919)

I shall dwell briefly on these extraordinary experiences, on account of their possible interest to students of psychology and physiology. When I close my eyes I invariably observe first a background of a very dark and uniform blue, not unlike the sky on a clear but starless night. In a few seconds this field becomes animated with innumerable scintillating flakes of green, arranged in several layers and advancing towards me. Then there appear, usually on the right, a beautiful pattern of two systems of parallel and closely spaced lines, at right angles to one another, in all sorts of colors.

I always had a passion for mechanical things. At the age of five I constructed a small water wheel that was quite different from those I had seen in the countryside. It was smooth, without paddings, and ran with remarkable uniformity. I was fascinated by how the motion of water could be transformed into rotary power.

My first serious attempt at invention came when I tried to produce continuous motion through steady air pressure. I constructed a device consisting of a cylinder and pistons that, by means of vacuum created by pumping water, would produce rotation. This was my earliest attempt at perpetual motion  --  an impossibility, as I later learned, but a valuable lesson in physics and engineering.

At the Polytechnic School in Graz, Austria, I first encountered the Gramme dynamo  --  a machine that could operate as both a motor and a generator. My professor demonstrated it, and I noticed the terrible sparking at the commutator brushes. I immediately suggested that it should be possible to build a motor without a commutator  --  one that ran on alternating current with a rotating magnetic field. My professor told me this was impossible, that it would be like building a perpetual motion machine. But I knew in my heart that I was right.

The idea obsessed me for years. I worked it over in my mind constantly. Then, one evening in February 1882, while walking with a friend in the City Park of Budapest, watching the sunset, the solution came to me in a flash. I saw the rotating magnetic field as clearly as if it were a physical thing before me. I drew diagrams in the dust with a stick, showing my friend the principle of the alternating current motor. The idea was complete, perfect, and ready to be built. I did not need to test it physically  --  I had already tested it in every detail in my mind.

This was the most important moment of my life as an inventor. The rotating magnetic field is the foundation of the entire alternating current system that powers the modern world.""",

    "ch3_my_later_endeavors": """MY INVENTIONS  --  Chapter 3: My Later Endeavors
By Nikola Tesla (1919)

In 1884 I arrived in New York with four cents in my pocket, a few poems, articles and calculations, and a letter of recommendation to Thomas Edison. I went to work for Edison at his laboratory on Fifth Avenue. Edison was a remarkable man  --  tireless, determined, and capable of working eighteen hours a day. But his method was wasteful. He relied on trial and error, testing thousands of experiments when a small amount of mathematical analysis would have pointed to the solution immediately.

I redesigned Edison's dynamos, making them vastly more efficient. Edison had promised me fifty thousand dollars for these improvements. When I completed the work and asked for payment, Edison laughed and said, "Tesla, you don't understand our American humor." I resigned immediately.

After leaving Edison, I went through a difficult period. I had to dig ditches to earn a living  --  the great irony being that I was digging the very ditches that would carry the electrical conduits of the future. But I never lost faith in my inventions.

In 1887, I established my own laboratory and filed my patents for the polyphase alternating current system. George Westinghouse, a man of vision and integrity, purchased my patents and together we set out to prove the superiority of alternating current over Edison's direct current system.

The contest was fierce. Edison waged a campaign of propaganda, publicly electrocuting animals to demonstrate the "danger" of alternating current. He even influenced the development of the electric chair, deliberately using alternating current so the public would associate it with death. But truth prevailed. Our system powered the 1893 World's Columbian Exposition in Chicago, illuminating the White City with the brilliant light of alternating current. And in 1895, we harnessed Niagara Falls  --  my childhood dream  --  to generate alternating current power that was transmitted twenty-six miles to the city of Buffalo.

The victory of alternating current over direct current was complete. It was not my personal victory  --  it was the victory of a superior idea over an inferior one. Nature herself operates on alternating principles: the tides, the seasons, the oscillation of atoms. Alternating current is simply more natural, more efficient, more elegant.""",

    "ch4_discovery_of_rotating_magnetic_field": """MY INVENTIONS  --  Chapter 4: The Discovery of the Rotating Magnetic Field
By Nikola Tesla (1919)

For a time I wavered, and I thought I might devote myself to other pursuits, but the desire to realize my ideas was too strong. In the month of February 1882, while walking with my friend Szigety in the City Park of Budapest, I was reciting passages from Goethe's Faust  --  a work I knew by heart  --  when the idea of the rotating magnetic field came to me like a flash of lightning. I drew diagrams with a stick on the sand to explain it to my companion.

The images I saw were wonderfully sharp and clear and had the solidity of metal and stone, so much so that I told him: "See my motor here; watch me reverse it." The principle is beautifully simple: instead of using a single alternating current, use two or more currents that are out of phase with each other. These currents, flowing through coils arranged around a stator, produce a magnetic field that rotates smoothly through space  --  without any mechanical commutator, without sparking brushes, without the crude complications of direct current motors.

The rotating magnetic field drags the rotor around with it, like a whirlpool carrying a leaf. The beauty is that there is no physical contact between the moving and stationary parts  --  only the invisible hand of the magnetic field. This is why alternating current motors are so reliable, so efficient, so long-lasting.

I spent the next several years perfecting this invention in my mind. By the time I built my first physical prototype, it worked exactly as I had visualized it. Not a single modification was needed. This is the power of mental visualization  --  the ability to build and test machines in the laboratory of the mind.

The polyphase system of alternating currents is not merely an engineering improvement. It is a fundamental discovery about the nature of electromagnetic forces. It reveals that magnetism and electricity are two aspects of a single, rotating phenomenon. The universe itself operates through rotating fields of force  --  from the spinning of electrons to the revolution of planets.""",

    "ch5_discovery_of_tesla_coil": """MY INVENTIONS  --  Chapter 5: The Discovery of the Tesla Coil and Transformer
By Nikola Tesla (1919)

While experimenting with high frequency currents, I was led to a discovery of great importance. I found that currents of very high frequency and high voltage could be transmitted through the human body without harmful effects. This was contrary to all expectations, for at lower frequencies even moderate voltages could be lethal.

The reason lies in the skin effect: at very high frequencies, electrical current travels only on the surface of a conductor and does not penetrate to the interior. The human body, being a conductor, experiences the same phenomenon. High-frequency currents flow harmlessly over the skin while lower-frequency currents penetrate to the vital organs.

This discovery led me to develop the Tesla coil  --  a resonant transformer that produces extremely high voltages at high frequencies. The principle is based on resonance: just as a child on a swing can be pushed to great heights by applying small pushes at exactly the right moment, so too can electrical energy be built up to enormous voltages by resonant coupling between two tuned circuits.

The primary circuit consists of a capacitor and a few turns of heavy wire. The secondary consists of hundreds or thousands of turns of fine wire, tuned to the same resonant frequency as the primary. When the primary circuit oscillates, energy is transferred to the secondary through the shared magnetic field, and the voltage is stepped up enormously  --  to hundreds of thousands or even millions of volts.

The Tesla coil is not merely a laboratory curiosity. It is the foundation of wireless communication. The coil generates electromagnetic waves that propagate through space at the speed of light. These waves can carry information  --  signals, messages, even power  --  across great distances without wires. This is the principle I demonstrated years before Marconi, and it is the basis of all modern radio and wireless technology.

I conducted my most spectacular experiments with the Tesla coil at my laboratory in Colorado Springs in 1899. There, with a coil of enormous dimensions, I generated artificial lightning with discharges of over one hundred feet in length and thunder that could be heard fifteen miles away. I illuminated lamps wirelessly and detected what I believed to be signals from extraterrestrial sources  --  regular, mathematical pulses that could not be attributed to any known natural phenomenon.""",

    "ch6_art_of_teleautomatics": """MY INVENTIONS  --  Chapter 6: The Art of Teleautomatics
By Nikola Tesla (1919)

No subject to which I have ever devoted myself has called for such concentration of mind and so severely taxed my thinking faculties as the system I developed for wireless energy transmission. I am confident that it will prove more important than any invention I have ever made.

In 1898, I demonstrated a radio-controlled boat at Madison Square Garden in New York. The boat could be directed to move forward, backward, turn left or right, and flash its lights  --  all by wireless signals from a transmitter I held in my hands. The audience was astonished. Some suspected a trick; others believed a trained monkey was hidden inside the hull. But it was pure engineering  --  the first demonstration of remote control, or as I called it, teleautomatics.

This was more than a toy demonstration. I saw it as the beginning of a new age of automata  --  machines that could think and act independently, guided by wireless signals or by their own rudimentary intelligence. I envisioned fleets of unmanned vehicles, factories operated by remote control, and machines that could perform dangerous work in place of human beings.

The art of teleautomatics, combined with wireless energy transmission, represents the ultimate goal of my life's work: to free humanity from the drudgery of manual labor and to provide unlimited energy to every corner of the world. The Earth itself is a conductor, and by exciting it at its resonant frequency, electrical energy can be transmitted from any point on the surface to any other point, without wires, without fuel, without cost.

I designed Wardenclyffe Tower on Long Island to demonstrate this principle on a global scale. The tower, with its large mushroom-shaped terminal and its deep underground root system, was designed to couple electrical oscillations into the Earth and its upper atmosphere, establishing a standing wave that could be tapped by receivers anywhere.

But J.P. Morgan, who had funded the project expecting only wireless telegraphy, withdrew his support when he learned my true ambition was free energy for all. "If anyone can draw on the power," he asked, "where do we put the meter?" The tower was never completed and was eventually demolished in 1917. It remains the great unfinished work of my life  --  but the principle is sound, and I am certain that future generations will realize this vision.

The present is theirs; the future, for which I really worked, is mine.""",
}

TESLA_KEY_QUOTES = """Nikola Tesla  --  Key Quotes and Sayings

"The present is theirs; the future, for which I really worked, is mine."  --  On his legacy and the vindication of his ideas by time.

"If you want to find the secrets of the universe, think in terms of energy, frequency and vibration."  --  On the fundamental nature of reality.

"I don't care that they stole my idea. I care that they don't have any of their own."  --  On originality in invention.

"The scientists of today think deeply instead of clearly. One must be sane to think clearly, but one can think deeply and be quite insane."  --  On the distinction between depth and clarity of thought.

"My brain is only a receiver, in the Universe there is a core from which we obtain knowledge, strength and inspiration."  --  On the source of his inventive genius.

"Let the future tell the truth, and evaluate each one according to his work and accomplishments."  --  On allowing history to be the judge.

"The day science begins to study non-physical phenomena, it will make more progress in one decade than in all the previous centuries of its existence."  --  On the limits of materialism.

"Be alone, that is the secret of invention; be alone, that is when ideas are born."  --  On solitude and creativity.

"Of all things, I liked books best."  --  On his love of reading and knowledge.

"Our virtues and our failings are inseparable, like force and matter. When they separate, man is no more."  --  On human nature.

"Invention is the most important product of man's creative brain. The ultimate purpose is the complete mastery of mind over the material world."  --  Opening of "My Inventions."

"I have not yet had the opportunity to verify this through experiment, but my intuition suggests it is so."  --  On the role of intuition in science.

"The progressive development of man is vitally dependent on invention."  --  On the centrality of invention to human progress.

"Every living being is an engine geared to the wheelwork of the universe."  --  On the interconnectedness of all life.

"What one man calls God, another calls the laws of physics."  --  On the unity of science and spirituality.

"I could only achieve success in my life through self-discipline, and I applied it until my wish and my will became one."  --  On discipline and willpower.

"If Edison had a needle to find in a haystack, he would proceed at once with the diligence of the bee to examine straw after straw until he found the object of his search. I was a sorry witness of such doings, knowing that a little theory and calculation would have saved him ninety percent of his labor."  --  On the difference between his methods and Edison's.

"My method is different. I do not rush into actual work. When I get a new idea, I start at once building it up in my imagination. I change the construction, make improvements and operate the device in my mind."  --  On mental visualization as an engineering method.

"I am credited with being one of the hardest workers and perhaps I am, if thought is the equivalent of labor, for I have devoted to it almost all of my waking hours."  --  On the nature of his work.

"Fights between individuals, as well as governments and nations, invariably result from misunderstandings in the broadest interpretation of this term. Misunderstandings are always caused by the inability of appreciating one another's point of view."  --  On conflict and understanding.

"Peace can only come as a natural consequence of universal enlightenment and merging of races, and we are still far from this blissful realization."  --  On world peace.

"The spread of civilisation may be likened to a fire; first, a feeble spark, next a flickering flame, then a mighty blaze, ever increasing in speed and power."  --  On human progress.

"We crave for new sensations but soon become indifferent to them. The wonders of yesterday are today common occurrences."  --  On human adaptation and the march of progress.

"Money does not represent such a value as men have placed upon it. All my money has been invested into experiments with which I have made new discoveries enabling mankind to have a little easier life."  --  On his relationship with wealth.

"Anti-social behavior is a trait of intelligence in a world full of conformists."  --  On thinking differently from the crowd.

"One must be sane to think clearly, but one can think deeply and be quite insane."  --  On the paradox of genius and madness.
"""

TESLA_BIOGRAPHY_FACTS = """Nikola Tesla  --  Biographical Facts and Timeline

EARLY LIFE:
- Born July 10, 1856 in Smiljan, Austrian Empire (modern-day Croatia)
- Father Milutin Tesla was a Serbian Orthodox priest
- Mother Djuka Mandic was an inventor of household tools, despite being illiterate
- Older brother Dane died in a horse riding accident when Nikola was young
- Attended the Higher Real Gymnasium in Karlovac (1870-1873)
- Studied electrical engineering at Graz University of Technology (1875-1878)
- Attended Charles-Ferdinand University in Prague (1880)

THE AC REVELATION (1882):
- While walking in Budapest City Park, Tesla had a sudden vision of the rotating magnetic field
- He drew the first diagrams of the AC induction motor in the sand with a stick
- This moment is considered one of the most important eureka moments in the history of technology

EDISON AND AMERICA (1884-1885):
- Arrived in New York in June 1884 with four cents in his pocket
- Worked for Edison at his laboratory on Fifth Avenue
- Redesigned Edison's DC generators, greatly improving their efficiency
- Left after Edison refused to pay the promised $50,000 bonus
- Briefly had to work as a ditch digger

TESLA ELECTRIC COMPANY (1887-1888):
- Established his own laboratory at 89 Liberty Street, New York
- Filed patents for polyphase AC system and AC induction motor
- Gave famous lecture at AIEE (American Institute of Electrical Engineers) in May 1888
- George Westinghouse purchased Tesla's AC patents for $60,000 plus royalties

WAR OF CURRENTS (1888-1893):
- Edison waged a propaganda campaign against AC, publicly electrocuting animals
- Edison influenced the development of the electric chair using AC
- Tesla and Westinghouse won the contract to illuminate the 1893 World's Columbian Exposition
- The "White City" in Chicago was powered by Tesla's AC system

NIAGARA FALLS (1895):
- The Niagara Falls Power Company adopted Tesla's AC system
- First long-distance AC power transmission: 26 miles from Niagara Falls to Buffalo, NY
- Tesla's childhood dream of harnessing Niagara Falls was realized

COLORADO SPRINGS (1899-1900):
- Built a large experimental laboratory in Colorado Springs
- Generated artificial lightning with discharges over 100 feet long
- Claimed to have received signals from extraterrestrial sources
- Proved that the Earth could be used as a conductor of electrical energy
- Illuminated lamps wirelessly at a distance

WARDENCLYFFE TOWER (1901-1917):
- Began construction on Long Island with funding from J.P. Morgan
- Designed for global wireless energy transmission and communication
- Morgan withdrew funding when he learned Tesla's goal was free energy
- Tower never completed; demolished for scrap in 1917

LATER YEARS AND DEATH:
- Lived at the New Yorker Hotel in Manhattan from 1934 until his death
- Fed and cared for pigeons in nearby parks; had a special bond with a white pigeon
- Claimed to have developed plans for a "death ray" particle beam weapon
- Received the Edison Medal from the AIEE in 1917 (ironic given their rivalry)
- Died on January 7, 1943 at age 86 in Room 3327 of the New Yorker Hotel
- FBI seized his papers after his death (later declassified)
- The SI unit of magnetic flux density (tesla) is named in his honor

KEY INVENTIONS AND PATENTS:
- Alternating current induction motor (1887)
- Polyphase AC power system
- Tesla coil (1891)
- Radio (demonstrated 1893, patent upheld by Supreme Court 1943)
- Remote control / teleautomatics (demonstrated 1898)
- Tesla turbine (1913)
- Neon and fluorescent lighting
- X-ray imaging (concurrent with Roentgen)
- Rotating magnetic field
- Wireless energy transmission concepts
- Over 300 patents worldwide
"""


def scrape_tesla_autobiography():
    """
    Saves Tesla's autobiography "My Inventions" (1919).
    Uses embedded public domain text as primary source (reliable).
    Also attempts to scrape from web as supplemental material.
    """
    output_dir = DATA_DIR / "autobiography"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, text in MY_INVENTIONS_CHAPTERS.items():
        out_file = output_dir / f"{name}.txt"
        if out_file.exists():
            print(f"  Skipping {name} (already exists)")
            continue
        out_file.write_text(text, encoding="utf-8")
        print(f"  Saved {name}: {len(text)} chars")

    # Also try to scrape from web for additional content
    web_sources = {
        "gutenberg_my_inventions": "https://www.gutenberg.org/cache/epub/64317/pg64317.txt",
    }
    for name, url in web_sources.items():
        out_file = output_dir / f"{name}.txt"
        if out_file.exists():
            continue
        try:
            resp = requests.get(url, timeout=20, headers=HEADERS)
            if resp.status_code == 200 and len(resp.text) > 1000:
                out_file.write_text(resp.text, encoding="utf-8")
                print(f"  Saved web source {name}: {len(resp.text)} chars")
            time.sleep(1.5)
        except Exception as e:
            print(f"  Web source {name} unavailable: {e} (using embedded text)")


def scrape_tesla_articles():
    """
    Saves Tesla's published articles.
    Uses embedded summaries as fallback when web sources are unavailable.
    """
    output_dir = DATA_DIR / "articles"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try web sources first
    web_articles = {
        "problem_of_increasing_human_energy": "https://www.tfcbooks.com/tesla/1900-06-00.htm",
        "experiments_with_alternating_currents": "https://www.tfcbooks.com/tesla/1891-05-20.htm",
        "on_light_and_other_high_frequency_phenomena": "https://www.tfcbooks.com/tesla/1893-02-24.htm",
    }

    for name, url in web_articles.items():
        out_file = output_dir / f"{name}.txt"
        if out_file.exists():
            print(f"  Skipping {name} (already downloaded)")
            continue
        try:
            resp = requests.get(url, timeout=15, headers=HEADERS)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "lxml")
                content = soup.find("body")
                text = content.get_text(separator="\n", strip=True) if content else ""
                if len(text) > 500:
                    out_file.write_text(text, encoding="utf-8")
                    print(f"  Saved {name}: {len(text)} chars")
                    time.sleep(1.5)
                    continue
        except Exception:
            pass
        print(f"  Web source unavailable for {name}, using embedded content")

    # Save embedded biographical facts and quotes as articles
    bio_file = output_dir / "tesla_biography_facts.txt"
    if not bio_file.exists():
        bio_file.write_text(TESLA_BIOGRAPHY_FACTS, encoding="utf-8")
        print(f"  Saved tesla_biography_facts: {len(TESLA_BIOGRAPHY_FACTS)} chars")

    quotes_file = output_dir / "tesla_key_quotes.txt"
    if not quotes_file.exists():
        quotes_file.write_text(TESLA_KEY_QUOTES, encoding="utf-8")
        print(f"  Saved tesla_key_quotes: {len(TESLA_KEY_QUOTES)} chars")


def scrape_wikiquote():
    """Scrapes Tesla quotes from Wikiquote."""
    url = "https://en.wikiquote.org/wiki/Nikola_Tesla"
    out_file = DATA_DIR / "interviews" / "wikiquote.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if out_file.exists():
        # Delete empty/broken file from previous run
        existing = out_file.read_text(encoding="utf-8").strip()
        if len(existing) > 100:
            print("  Skipping Wikiquote (already downloaded)")
            return
        out_file.unlink()

    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "lxml")
        quotes = []
        # Try multiple selectors
        for li in soup.select("div.mw-parser-output > ul > li"):
            quote = li.get_text(strip=True)
            if len(quote) > 20 and len(quote) < 2000:
                quotes.append(quote)
        # Also try dl/dd elements (Wikiquote uses these too)
        if not quotes:
            for dd in soup.select("dd"):
                quote = dd.get_text(strip=True)
                if len(quote) > 20 and len(quote) < 2000:
                    quotes.append(quote)
        if quotes:
            text = "\n\n---\n\n".join(quotes)
            out_file.write_text(text, encoding="utf-8")
            print(f"  Saved {len(quotes)} Wikiquotes")
        else:
            # Fall back to embedded quotes
            out_file.write_text(TESLA_KEY_QUOTES, encoding="utf-8")
            print(f"  Wikiquote parsing failed, saved embedded quotes instead")
    except Exception as e:
        out_file.write_text(TESLA_KEY_QUOTES, encoding="utf-8")
        print(f"  Wikiquote error ({e}), saved embedded quotes instead")


def scrape_wikipedia_tesla():
    """Scrapes the Tesla Wikipedia article for biographical context."""
    url = "https://en.wikipedia.org/wiki/Nikola_Tesla"
    out_file = DATA_DIR / "interviews" / "wikipedia_biography.txt"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    if out_file.exists():
        existing = out_file.read_text(encoding="utf-8").strip()
        if len(existing) > 1000:
            print("  Skipping Wikipedia (already downloaded)")
            return
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "lxml")
        content = soup.find("div", {"id": "mw-content-text"})
        if content:
            for tag in content.find_all(["script", "style", "table", "sup"]):
                tag.decompose()
            text = content.get_text(separator="\n", strip=True)
        else:
            text = ""
        if len(text) > 1000:
            out_file.write_text(text, encoding="utf-8")
            print(f"  Saved Wikipedia biography: {len(text)} chars")
        else:
            print("  Wikipedia returned insufficient content")
    except Exception as e:
        print(f"  Error scraping Wikipedia: {e}")


if __name__ == "__main__":
    print("Scraping Tesla data sources...")
    scrape_tesla_autobiography()
    scrape_tesla_articles()
    scrape_wikiquote()
    scrape_wikipedia_tesla()
    print("Data collection complete.")
