import uuid

import pytest

from tests.functional.utils.models import Person, PersonFilm

_PERSONS_INDEX_NAME = "personas"


@pytest.mark.asyncio
@pytest.mark.usefixtures('persons_index')
async def test_get_existing_person_by_id(es_write_data, make_get_request):
    person_id = uuid.uuid4()
    person = Person(
        uuid=person_id,
        full_name='full name',
        films=[
            PersonFilm(uuid=uuid.uuid4(), roles=['writer', 'director']),
            PersonFilm(uuid=uuid.uuid4(), roles=['actor']),
        ]
    )
    await es_write_data([{'_index': _PERSONS_INDEX_NAME, '_id': str(person_id), '_source': person.model_dump(by_alias=True)}])

    response = await make_get_request(f'api/v1/persons/{person_id}')

    assert response.status == 200
    body = await response.json()
    assert person == Person(**body)
