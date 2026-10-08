package com.korpodrony.dao;

import com.korpodrony.model.User;

import java.util.List;
import java.util.Set;

public interface UserRepositoryDao {

    boolean createUser(String name, String surname);

    boolean deleteUser(int userID);

    User getUser(int userID);

    boolean editUser(int userID, String name, String surname);

    default List<Integer> getAllUsersIDs() {
        return null;
    }

    List<User> getAllUsers();

    default boolean hasUser(User user) {
        return false;
    }

    boolean hasUserWithThisID(int userID);

    default Set<User> getUsersSet() {
        return null;
    }
}
