package com.korpodrony.repository;

import com.korpodrony.model.Organization;

import javax.ejb.Stateless;

@Stateless
public class OrganizationRepository {
    private static Organization organizationRepository = new Organization();

    public static Organization getOrganizationRepository() {
        return organizationRepository;
    }

    public static void setOrganizationRepository(Organization organization) {
        OrganizationRepository.organizationRepository = organization;
    }
}