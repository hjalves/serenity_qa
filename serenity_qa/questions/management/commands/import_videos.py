import logging

from django.core.management.base import BaseCommand

from serenity_qa.questions.models import Video

logger = logging.getLogger(__name__)


VIDEO_CODES = [
    "qInX9Ciikaw",
    "ub8ZYDGwkwk",
    "X6Vt8ASpVV4",
    "3_yYQlTlJ1A",
    "i1qhDA6Sgn8",
    "emt7mEuWGcE",
    "MnZqD1eAQrc",
    "8kNuD0nvqSs",
    "Fagn3BpUgiQ",
    "puTsBKAQzk4",
    "PM26Ax3F8jw",
    "9PB1SS5TwGg",
    "yWuSWrmqJj4",
    "cSZgd5VV8is",
    "TnKq_q24fO8",
    "tO46UwcMj6Q",
    "Sdg-FP_unGE",
    "SPUkXtSri1U",
    "aabIlXbB9yU",
    "zTe6UUwMo7Q",
    "i2U5M8ktaf4",
    "BdD1Wzu6l1s",
    "pEslaE_Dn2c",
    "E6Eiw0dNRGE",
    "cKHuME1v5ic",
    "Z12_aX1tmx0",
    "edZ-uyBGmrg",
    "XLNY1ZR6S7w",
    "WhV4YJ7LSkY",
    "DA1Ch0tvRoI",
    "GJbhKIUQYMc",
    "lYeO57oFSlE",
    "aZlTs-UoulE",
    "gpC4Jm0lq3E",
    "e1_Lr2BCSMI",
    "Xa5_tW_eovM",
    "KAEnwWMGNhM",
    "vMYhD0J2nD0",
    "aT7KjpUyhik",
    "rQKlgDQ7RvI",
    "s8apJg4mbmo",
    "9U9rv4TqY80",
    "59uvzDRfYgc",
    "-Unnb55G8RA",
    "u-nXBDF2ExI",
    "dfobZPonzUg",
    "puNKFf_yCHM",
    "nWHoegNHXC4",
    "h3IasVVL_k0",
    "pSfTiLMyUsY",
    "0M_nSzXwZ1M",
    "35kkyQw_Ges",
    "RajnoOkYg04",
    "8dDHV9DqZh4",
    "xX7Xh3uaC8I",
    "hcYt1ZKqyoE",
    "64LylDGuzDc",
    "090Fgq4YMPU",
    "HNQhn0d3ri8",
    "dYE6Cc7-kOA",
    "cfPYp3kKbjY",
    "3t3SO2dxw3s",
    "mGHRpHjMqbM",
    "UDGd4j99PaM",
    "dB88MoBg4no",
    "xj6fYHrIyqM",
    "gmwO9sEr3fg",
]


class Command(BaseCommand):
    help = "Initial video import"

    def handle(self, *args, **options):
        for code in VIDEO_CODES:
            self.stdout.write(f"Video: code={code}", ending="")
            video, created = Video.objects.get_or_create(code=code)
            self.stdout.write(f" id={video.id} created={created}")
