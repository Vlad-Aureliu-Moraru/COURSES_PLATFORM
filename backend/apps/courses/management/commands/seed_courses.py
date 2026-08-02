import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.courses.models import Course, Lesson


class Command(BaseCommand):
    help = 'Seed the course and lessons from the markdown module files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='../',
            help='Path to the directory containing module markdown files.',
        )

    def handle(self, *args, **options):
        base = Path(options['path']).resolve()
        files = sorted(base.glob('[0-9][0-9]-*.md'))

        course, created = Course.objects.get_or_create(
            slug='bani-online',
            defaults={
                'title': 'BaniOnline — Curs practic de bani online',
                'description': (
                    'Curs complet pentru începători: micro-taskuri, sondaje, '
                    'platforme verificate și un plan de 30 de zile.'
                ),
            },
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found"} course: {course.slug}'))

        for path in files:
            frontmatter = self._parse_frontmatter(path)
            slug = path.stem  # e.g. "02-micro-taskuri"
            lesson, lesson_created = Lesson.objects.update_or_create(
                course=course,
                slug=slug,
                defaults={
                    'title': frontmatter.get('title', slug),
                    'order': int(frontmatter.get('order', 0)),
                    'est_time': frontmatter.get('est_time', ''),
                    'is_free': frontmatter.get('free', 'false').strip().lower() == 'true',
                    'is_published': True,
                },
            )
            status = 'Created' if lesson_created else 'Updated'
            self.stdout.write(f'  {status} lesson: {lesson.slug}')

        self.stdout.write(self.style.SUCCESS(f'Done. {len(files)} lessons in course.'))

    def _parse_frontmatter(self, path):
        text = path.read_text(encoding='utf-8')
        match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
        if not match:
            return {}
        result = {}
        for key, value in re.findall(r'^(\w+):\s*(.+)$', match.group(1), re.MULTILINE):
            value = value.strip().strip('"\'')
            result[key] = value
        return result
