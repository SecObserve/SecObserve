# Architecture

![How it is build](assets/images/../../../assets/images/secobserve_architecture.svg){ align=center, width="800" }

## Frontend

The frontend is a single page application (SPA), implemented with TypeScript, React and the [React-Admin framework](https://marmelab.com/react-admin). The page is delivered by a nginx server.

## Backend

The backend is implemented with Python and [Django](https://www.djangoproject.com) / [Django Rest Framework](https://www.django-rest-framework.org). A Gunicorn server delivers the REST API that is used by the frontend to show and manipulate data and by CI/CD pipelines to upload scan results.

## Database

Currently MySQL and PostgreSQL are supported as databases. The [full text search](../usage/full_text_search.md) for observations is only available with PostgreSQL.
