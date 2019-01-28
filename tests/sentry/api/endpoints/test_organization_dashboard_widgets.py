from __future__ import absolute_import

from django.core.urlresolvers import reverse

from sentry.models import Widget, WidgetDataSource, WidgetDisplayTypes
from sentry.testutils import OrganizationDashboardWidgetTestCase


class OrganizationDashboardWidgetsPostTestCase(OrganizationDashboardWidgetTestCase):
    def url(self, dashboard_id):
        return reverse(
            'sentry-api-0-organization-dashboard-widgets',
            kwargs={
                'organization_slug': self.organization.slug,
                'dashboard_id': dashboard_id,
            }
        )

    def test_simple(self):
        data_sources = [
            {
                'name': 'knownUsersAffectedQuery_2',
                'data': self.known_users_query,
                'type': 'discover_saved_search',
                'order': 1,
            },
            {
                'name': 'anonymousUsersAffectedQuery_2',
                'data': self.anon_users_query,
                'type': 'discover_saved_search',
                'order': 2
            },
        ]
        response = self.client.post(
            self.url(self.dashboard.id),
            data={
                'dashboard_id': self.dashboard.id,
                'displayType': 'line',
                'title': 'User Happiness',
                'dataSources': data_sources,
            }
        )

        assert response.status_code == 201

        self.assert_widget_data(
            response.data,
            order='1',
            title='User Happiness',
            display_type='line',
            data_sources=data_sources,
        )

        widgets = Widget.objects.filter(
            dashboard_id=self.dashboard.id
        )
        assert len(widgets) == 1

        self.assert_widget(
            widgets[0],
            order=1,
            title='User Happiness',
            display_type=WidgetDisplayTypes.LINE_CHART,
            data_sources=data_sources,
        )

    def test_widget_no_data_souces(self):
        response = self.client.post(
            self.url(self.dashboard.id),
            data={
                'dashboard_id': self.dashboard.id,
                'displayType': 'line',
                'title': 'User Happiness',
                # 'dataSources': [],
            }
        )
        assert response.status_code == 201
        self.assert_widget_data(
            response.data,
            order='1',
            title='User Happiness',
            display_type='line',
        )

        widgets = Widget.objects.filter(
            dashboard_id=self.dashboard.id
        )
        assert len(widgets) == 1

        self.assert_widget(
            widgets[0],
            order=1,
            title='User Happiness',
            display_type=WidgetDisplayTypes.LINE_CHART,
        )
        assert not WidgetDataSource.objects.filter(
            widget_id=widgets[0],
        ).exists()

    def test_new_widgets_added_to_end_of_dashboard_order(self):
        widget_1 = Widget.objects.create(
            order=1,
            title='Like a room without a roof',
            display_type=WidgetDisplayTypes.LINE_CHART,
            dashboard_id=self.dashboard.id,
        )
        widget_2 = Widget.objects.create(
            order=2,
            title='Hello World',
            display_type=WidgetDisplayTypes.LINE_CHART,
            dashboard_id=self.dashboard.id,
        )
        response = self.client.post(
            self.url(self.dashboard.id),
            data={
                'dashboard_id': self.dashboard.id,
                'displayType': 'line',
                'title': 'User Happiness',
            }
        )
        assert response.status_code == 201
        self.assert_widget_data(
            response.data,
            order='3',
            title='User Happiness',
            display_type='line',
        )
        widgets = Widget.objects.filter(
            dashboard_id=self.dashboard.id
        )
        assert len(widgets) == 3

        self.assert_widget(
            widgets.exclude(id__in=[widget_1.id, widget_2.id])[0],
            order=3,
            title='User Happiness',
            display_type=WidgetDisplayTypes.LINE_CHART,
            data_sources=None,
        )

    def test_unrecognized_display_type(self):
        response = self.client.post(
            self.url(self.dashboard.id),
            data={
                'dashboard_id': self.dashboard.id,
                'displayType': 'happy-face',
                'title': 'User Happiness',
            }
        )
        assert response.status_code == 400
        assert response.data == {'displayType': [u'Widget display_type happy-face not recognized.']}

    def test_unrecognized_data_source_type(self):
        response = self.client.post(
            self.url(self.dashboard.id),
            data={
                'dashboard_id': self.dashboard.id,
                'displayType': 'line',
                'title': 'User Happiness',
                'dataSources': [{
                    'name': 'knownUsersAffectedQuery_2',
                    'data': self.known_users_query,
                    'type': 'not-real-type',
                    'order': 1,
                }],
            }
        )
        assert response.status_code == 400
        assert response.data == {'dataSources': [
            u'type: Widget data source type not-real-type not recognized.']}
