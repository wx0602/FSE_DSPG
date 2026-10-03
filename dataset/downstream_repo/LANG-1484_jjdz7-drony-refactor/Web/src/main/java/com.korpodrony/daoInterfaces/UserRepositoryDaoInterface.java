package com.korpodrony.daoInterfaces;

import com.korpodrony.dto.AuthUserDTO;
import com.korpodrony.dto.UserDTO;
import com.korpodrony.entity.PermissionLevel;
import com.korpodrony.entity.UserEntity;

import javax.ejb.Local;
import java.util.List;

@Local
public interface UserRepositoryDaoInterface {

    int createUser(UserEntity userEntity);

    AuthUserDTO getAuthUserDTO(String email);

    List<UserDTO> getAllUsers();

    List<UserDTO> getUserDTObyName(String name);

    List<UserDTO> getUserDTObyName(String name, String surname);

    void updateUser(UserEntity userEntity);

    int getUserIdByEmail(String email);

    UserEntity getUserEntity(int userId);

    List<UserEntity> getAllUsersEntities();
}