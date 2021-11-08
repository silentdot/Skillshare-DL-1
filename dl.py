import sys
import os
from skillshare import Skillshare

# or by class ID:
# Skillshare.download_course_by_class_id(189505397)


def main():
    dl = Skillshare()
    course_url = sys.argv[1]
    dl.download_course_by_url(course_url)


if __name__ == "__main__":
    main()
