import logging

from django.core.management.base import BaseCommand

from serenity_qa.apps.questions.models import Video

logger = logging.getLogger(__name__)


VIDEO_CODES = [
    "gmwO9sEr3fg",
    "xj6fYHrIyqM",
    "dB88MoBg4no",
    "UDGd4j99PaM",
    "mGHRpHjMqbM",
    "3t3SO2dxw3s",
    "cfPYp3kKbjY",
    "dYE6Cc7-kOA",
    "HNQhn0d3ri8",
    "090Fgq4YMPU",
    "64LylDGuzDc",
    "hcYt1ZKqyoE",
    "xX7Xh3uaC8I",
    "8dDHV9DqZh4",
    "RajnoOkYg04",
    "35kkyQw_Ges",
    "0M_nSzXwZ1M",
    "pSfTiLMyUsY",
    "h3IasVVL_k0",
    "nWHoegNHXC4",
    "puNKFf_yCHM",
    "dfobZPonzUg",
    "u-nXBDF2ExI",
    "-Unnb55G8RA",
    "59uvzDRfYgc",
    "9U9rv4TqY80",
    "s8apJg4mbmo",
    "rQKlgDQ7RvI",
    "aT7KjpUyhik",
    "vMYhD0J2nD0",
    "KAEnwWMGNhM",
    "Xa5_tW_eovM",
    "e1_Lr2BCSMI",
    "gpC4Jm0lq3E",
    "aZlTs-UoulE",
    "lYeO57oFSlE",
    "GJbhKIUQYMc",
    "DA1Ch0tvRoI",
    "WhV4YJ7LSkY",
    "XLNY1ZR6S7w",
    "edZ-uyBGmrg",
    "Z12_aX1tmx0",
    "cKHuME1v5ic",
    "E6Eiw0dNRGE",
    "pEslaE_Dn2c",
    "BdD1Wzu6l1s",
    "i2U5M8ktaf4",
    "zTe6UUwMo7Q",
    "aabIlXbB9yU",
    "SPUkXtSri1U",
    "Sdg-FP_unGE",
    "tO46UwcMj6Q",
    "TnKq_q24fO8",
    "cSZgd5VV8is",
    "yWuSWrmqJj4",
    "9PB1SS5TwGg",
    "PM26Ax3F8jw",
    "puTsBKAQzk4",
    "Fagn3BpUgiQ",
    "8kNuD0nvqSs",
    "MnZqD1eAQrc",
    "emt7mEuWGcE",
    "i1qhDA6Sgn8",
    "3_yYQlTlJ1A",
    "X6Vt8ASpVV4",
    "ub8ZYDGwkwk",
    "qInX9Ciikaw",
]


class Command(BaseCommand):
    help = "Initial video import"

    def handle(self, *args, **options):
        for code in VIDEO_CODES:
            self.stdout.write(f"Video: code={code}", ending="")
            video, created = Video.objects.get_or_create(code=code)
            self.stdout.write(f" id={video.id} created={created}")
